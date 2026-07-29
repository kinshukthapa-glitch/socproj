from langchain_core.tools import tool
from langchain_groq import ChatGroq
from src.tools.security_tools import (
    alert_tools, endpoint_tools, identity_tools, incident_tools, reporting_tools, threat_hunting_tools
)
# Import the new RAG tool
from src.tools.knowledge_base import search_threat_intel

subagent_llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

@tool
def alert_analyst(query: str) -> str:
    """Handles security alerts, severity checks, and threat summaries."""
    search_fn, check_severity_fn = alert_tools[0], alert_tools[1]
    raw_alerts = search_fn.invoke({"query": query})
    
    # Query the ChromaDB knowledge base for context on this specific threat
    kb_context = search_threat_intel.invoke({"query": query})
    
    prompt = f"""
    You are the Alert Analysis Subagent.
    User Query: {query}
    SIEM Alerts Data: {raw_alerts}
    Knowledge Base Context (Threat Intel): {kb_context}
    
    CRITICAL INSTRUCTION: Analyze the alerts using the provided Knowledge Base Context. 
    You MUST completely ignore any context that is not directly related to the user's specific query or alert type.
    Respond in JSON format with keys: "analysis" (string) and "recommended_actions" (list of strings).
    Do not hallucinate external tools.
    """
    return subagent_llm.invoke(prompt).content

@tool
def endpoint_specialist(hostname: str) -> str:
    """Handles device status, malware detection, and endpoint health checks."""
    check_status_fn, malware_fn = endpoint_tools[0], endpoint_tools[1]
    status_data = check_status_fn.invoke({"hostname": hostname})
    malware_data = malware_fn.invoke({"hostname": hostname})
    
    prompt = f"""
    You are the Endpoint Specialist Subagent.
    Target Hostname: {hostname}
    Status Data: {status_data}
    Malware Data: {malware_data}
    
    Respond in JSON format with keys: "device_health" (string) and "isolation_required" (boolean).
    Do not hallucinate external tools.
    """
    return subagent_llm.invoke(prompt).content

@tool
def identity_specialist(username: str) -> str:
    """Handles login history, authentication events, and user activity checks."""
    login_fn, activity_fn = identity_tools[0], identity_tools[1]
    login_data = login_fn.invoke({"username": username})
    
    # Parse to check if user was found before calling second tool
    import json as _json
    login_parsed = _json.loads(login_data)
    if not login_parsed.get("found", True) is False:
        # User found — also fetch activity
        activity_data = activity_fn.invoke({"username": username})
    else:
        activity_data = login_data  # same "not found" payload

    prompt = f"""
    You are the Identity Specialist Subagent.
    Target Username: {username}
    Login History: {login_data}
    User Activity: {activity_data}

    CRITICAL INSTRUCTION:
    - If the Login History contains "found": false, you MUST respond ONLY with:
      {{"risk_assessment": "User '{username}' does not exist in the Identity Provider. No records found.", "anomalous_login_detected": false}}
      Do NOT make up any findings. Do NOT assume the user exists.
    - If the user IS found, provide a genuine risk assessment based strictly on the returned data.
    Respond in JSON format with keys: "risk_assessment" (string) and "anomalous_login_detected" (boolean).
    Do not hallucinate external tools.
    """
    return subagent_llm.invoke(prompt).content

@tool
def incident_specialist(title: str, severity: str) -> str:
    """Handles security incident creation, tracking, and escalation requests."""
    create_fn = incident_tools[0]
    result = create_fn.invoke({"title": title, "severity": severity})
    
    # Query the knowledge base for runbooks or SOPs related to this incident type
    kb_context = search_threat_intel.invoke({"query": title})
    
    prompt = f"""
    You are the Incident Management Subagent.
    Action Request: Create Incident Title='{title}', Severity='{severity}'
    Result Data: {result}
    Knowledge Base Context (Threat Intel): {kb_context}
    
    CRITICAL INSTRUCTION: Analyze the alerts using the provided Knowledge Base Context. 
    You MUST completely ignore any context that is not directly related to the user's specific query or alert type.
    
    Respond in JSON format with keys: "status" (string) and "incident_details" (string).
    Ensure the incident_details incorporate any relevant guidance from the Knowledge Base Context.
    Do not hallucinate external tools.
    """
    return subagent_llm.invoke(prompt).content

@tool
def reporting_specialist(incident_id: str) -> str:
    """Generates investigation reports, executive summaries, and incident timelines."""
    report_fn = reporting_tools[0]
    report_data = report_fn.invoke({"incident_id": incident_id})
    
    prompt = f"""
    You are the Reporting Subagent.
    Target Incident ID: {incident_id}
    Raw Report Data: {report_data}
    
    Respond in JSON format with keys: "executive_summary" (string) and "timeline" (list of strings).
    Do not hallucinate external tools.
    """
    return subagent_llm.invoke(prompt).content

@tool
def threat_hunter(query: str) -> str:
    """Handles multi-domain event correlation, threat hunting, and multi-stage attack detection."""
    query_fn = threat_hunting_tools[0]
    data = query_fn.invoke({"query": query})
    
    prompt = f"""
    You are the Threat Hunting & Correlation Subagent.
    Threat Hunt Query: {query}
    Correlated Data Lake Results: {data}
    
    CRITICAL INSTRUCTION: Analyze the provided correlated data.
    Respond in JSON format with keys: 
    - "attack_scenario" (string): brief description of the campaign
    - "risk_score" (float): from the data
    - "reasoning" (string): explainable reasoning for why these events are correlated
    - "recommended_actions" (list of strings): ordered containment and response steps
    Do not hallucinate external tools.
    """
    return subagent_llm.invoke(prompt).content

# All 6 domain subagents exported as tools for the supervisor
subagent_tools = [
    alert_analyst,
    endpoint_specialist,
    identity_specialist,
    incident_specialist,
    reporting_specialist,
    threat_hunter
]