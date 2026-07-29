from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver

from src.agents.subagents import subagent_tools

# Initialize the memory checkpointer
memory = MemorySaver()

# Define the state schema
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


# Bump this version string whenever supervisor logic changes.
# app.py checks this to force-rebuild the graph when the code changes.
GRAPH_VERSION = "v4"

def build_agent_executor():
    """Builds the main Supervisor agent using explicit graph routing."""

    # Phrases that explicitly authorise incident/report creation
    INCIDENT_TRIGGER_PHRASES = [
        "create an incident", "create incident", "open an incident",
        "raise an incident", "log an incident", "file an incident",
        "escalate", "file a report", "generate a report", "create a report",
        "make a report", "create a ticket",
    ]
    PROTECTED_TOOLS = {"incident_specialist", "reporting_specialist"}
    
    # 1. Initialize the powerful 70B model
    supervisor_llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
    
    # 2. ENFORCE SEQUENTIAL EXECUTION
    # This physically blocks the LLM from triggering multiple tools at once, forcing it to evaluate data first.
    llm_with_tools = supervisor_llm.bind_tools(subagent_tools, parallel_tool_calls=False)
    
    # 3. System Prompt
    sys_msg = (
        "You are the SecureOps AI SOC Supervisor.\n"
        "Your SOLE PURPOSE is to assist with cybersecurity operations, threat analysis, and incident response.\n\n"
        "DOMAIN SPECIALISTS:\n"
        "- alert_analyst: ONLY use for security alerts, SIEM searches, and alert severity.\n"
        "- endpoint_specialist: ONLY use for device health, OS status, and malware detection.\n"
        "- identity_specialist: ONLY use for user logins and user activity.\n"
        "- threat_hunter: ONLY use for multi-domain event correlation, threat hunting, and detecting coordinated multi-stage attacks.\n"
        "- incident_specialist: ONLY when user EXPLICITLY asks to create or escalate an incident.\n"
        "- reporting_specialist: ONLY when user EXPLICITLY asks to generate a report.\n\n"
        "CRITICAL RULES:\n"
        "0. OUT-OF-SCOPE GUARD (HIGHEST PRIORITY): If the user's message is NOT related to cybersecurity, threat detection, SOC operations, network security, malware, identity management, or incident response — you MUST respond ONLY with:\n"
        "   '⚠️ **Out of Scope**: I am SecureOps AI, a dedicated Cyber Threat Operations platform. I can only assist with security investigations, threat analysis, SIEM alerts, endpoint health, identity anomalies, and incident response. Please submit a security-related query.'\n"
        "   Do NOT call any tools. Do NOT attempt to answer. Examples of out-of-scope queries: greetings, personal questions, general knowledge, coding help, weather, names, jokes.\n"
        "1. STRICT SEQUENTIAL EXECUTION: You MUST ONLY call ONE tool at a time. NEVER call multiple tools in a single response. You must wait for the output of the first tool before calling the next.\n"
        "2. NO HALLUCINATIONS: Never invent parameters (like incident IDs or usernames). Wait for the actual data to be returned.\n"
        "3. NO PROACTIVE INCIDENT OR REPORT CREATION (CRITICAL): You MUST NEVER call incident_specialist or reporting_specialist unless the user has EXPLICITLY requested it using phrases like 'create an incident', 'escalate this', 'file a report', or 'generate a report'.\n"
        "   - Lookup queries (e.g. 'is there a user named X?', 'check host Y', 'what alerts exist?') → call the relevant specialist, summarise the returned data in plain Markdown, then STOP. Do NOT escalate.\n"
        "   - Threat-hunt queries that reveal risk → present findings with risk score and recommendations, then STOP and ASK the user if they want to create an incident.\n"
        "4. FINAL DELIVERABLE FOR FULL INVESTIGATIONS: When a full investigation is complete (only after using 2+ specialists on a real threat), output a comprehensive Executive Brief in Markdown:\n"
        "   - ### 🚨 Executive Incident Summary\n"
        "   - ### 📊 Telemetry & Evidence Breakdown (Markdown Table)\n"
        "   - ### 🧠 Threat Hunting & Risk Score (Risk Score 1.0–10.0 + Explainable Reasoning)\n"
        "   - ### 🛡️ Recommended Incident Response Actions (Numbered list)\n"
        "5. CANCELLATIONS/REJECTIONS: If a tool returns 'ACTION REJECTED' or 'blocked', immediately confirm the abort to the user. Do NOT generate any fallback data."
    )
    
    # 4. Define the Node Functions
    def chatbot(state: AgentState):
        """The main decision-making node."""
        from langchain_core.messages import HumanMessage, AIMessage

        messages = [{"role": "system", "content": sys_msg}] + state["messages"]
        response = llm_with_tools.invoke(messages)

        # ── Programmatic guardrail: block protected tools unless user explicitly asked ──
        # This runs in Python code and CANNOT be overridden by the LLM.
        if hasattr(response, "tool_calls") and response.tool_calls:
            # Collect all human message text from conversation history
            user_text = " ".join(
                m.content.lower()
                for m in state["messages"]
                if isinstance(m, HumanMessage) and isinstance(m.content, str)
            )
            explicitly_requested = any(
                phrase in user_text for phrase in INCIDENT_TRIGGER_PHRASES
            )

            # Strip any protected tool calls that weren't explicitly requested
            allowed_calls = [
                tc for tc in response.tool_calls
                if tc["name"] not in PROTECTED_TOOLS or explicitly_requested
            ]

            if len(allowed_calls) < len(response.tool_calls):
                # Some calls were blocked — return a clean refusal message instead
                blocked_names = [
                    tc["name"] for tc in response.tool_calls
                    if tc["name"] in PROTECTED_TOOLS and not explicitly_requested
                ]
                response = AIMessage(
                    content=(
                        f"ℹ️ I retrieved the requested data and completed the lookup. "
                        f"I have automatically blocked a call to `{'`, `'.join(blocked_names)}` "
                        f"because no explicit instruction to create an incident or report was given. "
                        f"If you'd like to escalate, please say **\"create an incident\"** or **\"generate a report\"**."
                    ),
                    tool_calls=allowed_calls,
                    id=response.id,
                )

        # Fallback: forcefully truncate tool calls if the model attempts to fire multiple at once
        if hasattr(response, "tool_calls") and len(response.tool_calls) > 1:
            first_call = response.tool_calls[0]
            response = AIMessage(
                content=response.content,
                tool_calls=[first_call],
                id=response.id
            )
            
        return {"messages": [response]}
        
    # 5. Build the Graph
    graph_builder = StateGraph(AgentState)
    
    # Add nodes
    graph_builder.add_node("chatbot", chatbot)
    graph_builder.add_node("tools", ToolNode(subagent_tools))
    
    # Add routing logic (tools_condition automatically checks if a tool was called)
    graph_builder.add_conditional_edges("chatbot", tools_condition)
    graph_builder.add_edge("tools", "chatbot")
    graph_builder.add_edge(START, "chatbot")
    
    # 6. Compile with HITL breakpoint
    agent_graph = graph_builder.compile(
        checkpointer=memory,           
        interrupt_before=["tools"]     
    )
    return agent_graph