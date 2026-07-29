import os
import uuid
import json
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# MUST be called at the very top before importing agent packages
load_dotenv()

import streamlit as st

# 1. MUST BE THE ABSOLUTE FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title="SecureOps AI | Cyber Threat Operations Console",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from src.agents.supervisor import build_agent_executor, GRAPH_VERSION

# ─────────────────────────────────────────────
#  CHAT HISTORY PERSISTENCE HELPERS
# ─────────────────────────────────────────────
CHAT_HISTORY_FILE = os.path.join(os.path.dirname(__file__), "chat_history.json")

def load_chat_history() -> dict:
    """Load persisted chat history from JSON file."""
    if os.path.exists(CHAT_HISTORY_FILE):
        try:
            with open(CHAT_HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}

def save_chat_history(history: dict) -> None:
    """Persist chat history dict to JSON file."""
    try:
        with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except OSError:
        pass

def auto_title(prompt: str, max_len: int = 32) -> str:
    """Generate a short display title from the first user prompt."""
    title = prompt.strip().replace("\n", " ")
    return (title[:max_len] + "…") if len(title) > max_len else title

# ─────────────────────────────────────────────
#  SESSION STATE INITIALIZATION
# ─────────────────────────────────────────────
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

if "chat_history" not in st.session_state:
    st.session_state.chat_history = load_chat_history()  # {chat_id: {title, thread_id, created_at}}

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None  # None until first message is sent

# Build the graph ONCE as a true singleton at module level.
if "supervisor_graph" not in st.session_state or st.session_state.get("graph_version") != GRAPH_VERSION:
    st.session_state.supervisor_graph = build_agent_executor()
    st.session_state.graph_version = GRAPH_VERSION
supervisor_graph = st.session_state.supervisor_graph

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
config = {"configurable": {"thread_id": st.session_state.thread_id}}

if "preset_prompt" not in st.session_state:
    st.session_state.preset_prompt = None

# ─────────────────────────────────────────────
#  DYNAMIC LIGHT & DARK GLASSMORPHISM DESIGN SYSTEM
# ─────────────────────────────────────────────
def get_theme_css(theme: str) -> str:
    if theme == "light":
        return """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap');

/* Smooth transition for theme fluctuation */
* {
    transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease !important;
}

header[data-testid="stHeader"] { visibility: hidden !important; height: 0 !important; }
footer { display: none !important; }
#MainMenu { visibility: hidden !important; }
.stDecoration { display: none !important; }
div[data-testid="stToolbar"] { visibility: hidden !important; }
section[data-testid="stSidebar"] { display: none !important; }
button[data-testid="baseButton-headerNoPadding"] { display: none !important; }

html, body, .stApp {
    background: #F8FAFC !important;
    background-image: 
        radial-gradient(at 0% 0%, rgba(6, 182, 212, 0.05) 0px, transparent 50%),
        radial-gradient(at 100% 100%, rgba(59, 130, 246, 0.04) 0px, transparent 50%),
        radial-gradient(at 50% 50%, rgba(139, 92, 246, 0.03) 0px, transparent 50%) !important;
    color: #0F172A !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    font-size: 14px;
    line-height: 1.6;
}

h1, h2, h3, h4, h5, h6 {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    letter-spacing: -0.02em !important;
}

.console-title {
    margin: 0 !important;
    font-size: 24px !important;
    font-weight: 800 !important;
    color: #0F172A !important;
}

.console-title .title-accent {
    color: #0284C7 !important;
}

.main .block-container {
    max-width: 980px !important;
    padding-top: 1.5rem !important;
    padding-bottom: 3rem !important;
    margin: 0 auto !important;
}

@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(12px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes pulseGlow {
    0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.6); }
    70% { box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
    100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
}

@keyframes pulseAmber {
    0% { box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.5); }
    70% { box-shadow: 0 0 0 10px rgba(245, 158, 11, 0); }
    100% { box-shadow: 0 0 0 0 rgba(245, 158, 11, 0); }
}

.status-dot-online {
    display: inline-block;
    width: 8px;
    height: 8px;
    background-color: #10B981;
    border-radius: 50%;
    margin-right: 8px;
    animation: pulseGlow 2s infinite;
}

.console-header-card {
    background: linear-gradient(135deg, #FFFFFF 0%, #F1F5F9 100%);
    backdrop-filter: blur(12px);
    border: 1px solid #CBD5E1;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.05);
    animation: fadeInUp 0.4s ease-out;
}

.metric-card {
    background: #FFFFFF;
    backdrop-filter: blur(8px);
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 0.85rem 1rem;
    text-align: center;
    transition: all 0.25s ease;
    animation: fadeInUp 0.5s ease-out;
}

.metric-card:hover {
    transform: translateY(-2px);
    border-color: #06B6D4;
    box-shadow: 0 4px 20px rgba(6, 182, 212, 0.15);
}

.metric-label {
    color: #64748B;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 4px;
}

.metric-value {
    color: #0F172A;
    font-size: 15px;
    font-weight: 700;
    font-family: 'Plus Jakarta Sans', sans-serif;
}

div[data-testid="stSegmentedControl"] {
    background-color: #F1F5F9 !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 10px !important;
    padding: 4px !important;
}

div[data-testid="stSegmentedControl"] button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    color: #475569 !important;
    transition: all 0.2s ease !important;
}

div[data-testid="stSegmentedControl"] button[aria-selected="true"] {
    background: linear-gradient(135deg, #06B6D4 0%, #2563EB 100%) !important;
    color: #FFFFFF !important;
    box-shadow: 0 2px 10px rgba(6, 182, 212, 0.3) !important;
}

div[data-testid="stChatMessage"] {
    background: #FFFFFF !important;
    backdrop-filter: blur(10px) !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 12px !important;
    padding: 1.25rem 1.5rem !important;
    margin-bottom: 1rem !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04) !important;
    animation: fadeInUp 0.35s ease-out !important;
}

div[data-testid="stChatMessage"]:hover {
    border-color: #CBD5E1 !important;
}

div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    border-left: 4px solid #2563EB !important;
    background: #F8FAFC !important;
}

div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
    border-left: 4px solid #0284C7 !important;
    background: #FFFFFF !important;
}

div[data-testid="stChatInput"] > div {
    background-color: #FFFFFF !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06) !important;
}

div[data-testid="stChatInput"] > div:focus-within {
    border-color: #0284C7 !important;
    box-shadow: 0 0 12px rgba(2, 132, 199, 0.2) !important;
}

div[data-testid="stChatInput"] textarea {
    color: #0F172A !important;
    font-family: 'Inter', sans-serif !important;
}

.approval-box {
    background: linear-gradient(135deg, #FEF3C7 0%, #FFFBEB 100%);
    border: 1px solid #F59E0B;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 0 20px rgba(245, 158, 11, 0.15);
    animation: fadeInUp 0.4s ease-out, pulseAmber 3s infinite;
    margin-top: 1rem;
    margin-bottom: 1.5rem;
    color: #1E293B !important;
}

.stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    border: 1px solid #CBD5E1 !important;
    background: #FFFFFF !important;
    color: #0F172A !important;
    transition: all 0.2s ease-in-out !important;
}

.stButton > button:hover {
    background: #F1F5F9 !important;
    border-color: #0284C7 !important;
    color: #0F172A !important;
    transform: translateY(-1px) !important;
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #06B6D4 0%, #2563EB 100%) !important;
    color: #FFFFFF !important;
    border: none !important;
    box-shadow: 0 4px 14px rgba(6, 182, 212, 0.3) !important;
}

.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #0891B2 0%, #1D4ED8 100%) !important;
    box-shadow: 0 6px 20px rgba(6, 182, 212, 0.45) !important;
    transform: translateY(-1px) !important;
}

code {
    color: #0284C7 !important;
    background-color: #F1F5F9 !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 6px !important;
    padding: 2px 6px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.85em !important;
}

div[data-testid="stCodeBlock"] pre {
    background-color: #F8FAFC !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 8px !important;
    font-family: 'JetBrains Mono', monospace !important;
}

div[data-testid="stForm"], div[data-testid="stBorderedContainer"] {
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 12px !important;
    padding: 1.5rem !important;
}

.stMarkdown, p {
    color: #334155;
}

.stCaption {
    color: #64748B !important;
}

/* ── Chat History Popover & Expander — LIGHT THEME ── */
button[data-testid="stPopoverButton"] {
    background: #FFFFFF !important;
    border: 1px solid #CBD5E1 !important;
    color: #0F172A !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    width: 100% !important;
    transition: all 0.2s ease !important;
}
button[data-testid="stPopoverButton"]:hover {
    background: #F1F5F9 !important;
    border-color: #0284C7 !important;
    color: #0284C7 !important;
}
div[data-testid="stPopover"] > div {
    background: #FFFFFF !important;
    border: 1px solid #CBD5E1 !important;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1) !important;
    border-radius: 12px !important;
    color: #0F172A !important;
}
div[data-testid="stPopover"] p,
div[data-testid="stPopover"] span,
div[data-testid="stPopover"] label {
    color: #334155 !important;
}
div[data-testid="stExpander"] {
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 10px !important;
}
div[data-testid="stExpander"] summary {
    color: #0F172A !important;
    font-weight: 600 !important;
}
div[data-testid="stExpander"] > div > div {
    background: #F8FAFC !important;
    color: #334155 !important;
}
</style>
"""
    else:
        return """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap');

/* Smooth transition for theme fluctuation */
* {
    transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease !important;
}

header[data-testid="stHeader"] { visibility: hidden !important; height: 0 !important; }
footer { display: none !important; }
#MainMenu { visibility: hidden !important; }
.stDecoration { display: none !important; }
div[data-testid="stToolbar"] { visibility: hidden !important; }
section[data-testid="stSidebar"] { display: none !important; }
button[data-testid="baseButton-headerNoPadding"] { display: none !important; }

html, body, .stApp {
    background: #0B0F17 !important;
    background-image: 
        radial-gradient(at 0% 0%, rgba(6, 182, 212, 0.08) 0px, transparent 50%),
        radial-gradient(at 100% 100%, rgba(59, 130, 246, 0.06) 0px, transparent 50%),
        radial-gradient(at 50% 50%, rgba(139, 92, 246, 0.04) 0px, transparent 50%) !important;
    color: #F1F5F9 !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    font-size: 14px;
    line-height: 1.6;
}

h1, h2, h3, h4, h5, h6 {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    letter-spacing: -0.02em !important;
}

.console-title {
    margin: 0 !important;
    font-size: 24px !important;
    font-weight: 800 !important;
    color: #FFFFFF !important;
}

.console-title .title-accent {
    color: #38BDF8 !important;
}

.main .block-container {
    max-width: 980px !important;
    padding-top: 1.5rem !important;
    padding-bottom: 3rem !important;
    margin: 0 auto !important;
}

@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(12px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes pulseGlow {
    0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.6); }
    70% { box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
    100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
}

@keyframes pulseAmber {
    0% { box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.5); }
    70% { box-shadow: 0 0 0 10px rgba(245, 158, 11, 0); }
    100% { box-shadow: 0 0 0 0 rgba(245, 158, 11, 0); }
}

.status-dot-online {
    display: inline-block;
    width: 8px;
    height: 8px;
    background-color: #10B981;
    border-radius: 50%;
    margin-right: 8px;
    animation: pulseGlow 2s infinite;
}

.console-header-card {
    background: linear-gradient(135deg, rgba(19, 27, 46, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    animation: fadeInUp 0.4s ease-out;
}

.metric-card {
    background: rgba(19, 27, 46, 0.6);
    backdrop-filter: blur(8px);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 10px;
    padding: 0.85rem 1rem;
    text-align: center;
    transition: all 0.25s ease;
    animation: fadeInUp 0.5s ease-out;
}

.metric-card:hover {
    transform: translateY(-2px);
    border-color: rgba(6, 182, 212, 0.3);
    box-shadow: 0 4px 20px rgba(6, 182, 212, 0.12);
}

.metric-label {
    color: #94A3B8;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 4px;
}

.metric-value {
    color: #F8FAFC;
    font-size: 15px;
    font-weight: 700;
    font-family: 'Plus Jakarta Sans', sans-serif;
}

div[data-testid="stSegmentedControl"] {
    background-color: rgba(15, 23, 42, 0.8) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 10px !important;
    padding: 4px !important;
    backdrop-filter: blur(8px);
}

div[data-testid="stSegmentedControl"] button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    color: #94A3B8 !important;
    transition: all 0.2s ease !important;
}

div[data-testid="stSegmentedControl"] button[aria-selected="true"] {
    background: linear-gradient(135deg, #06B6D4 0%, #2563EB 100%) !important;
    color: #FFFFFF !important;
    box-shadow: 0 2px 10px rgba(6, 182, 212, 0.3) !important;
}

div[data-testid="stChatMessage"] {
    background: rgba(19, 27, 46, 0.75) !important;
    backdrop-filter: blur(10px) !important;
    border: 1px solid rgba(255, 255, 255, 0.07) !important;
    border-radius: 12px !important;
    padding: 1.25rem 1.5rem !important;
    margin-bottom: 1rem !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25) !important;
    animation: fadeInUp 0.35s ease-out !important;
}

div[data-testid="stChatMessage"]:hover {
    border-color: rgba(255, 255, 255, 0.12) !important;
}

div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    border-left: 4px solid #3B82F6 !important;
    background: rgba(22, 32, 50, 0.8) !important;
}

div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
    border-left: 4px solid #06B6D4 !important;
    background: rgba(15, 23, 42, 0.85) !important;
}

div[data-testid="stChatInput"] > div {
    background-color: rgba(19, 27, 46, 0.9) !important;
    border: 1px solid rgba(6, 182, 212, 0.25) !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3) !important;
}

div[data-testid="stChatInput"] > div:focus-within {
    border-color: #06B6D4 !important;
    box-shadow: 0 0 15px rgba(6, 182, 212, 0.25) !important;
}

div[data-testid="stChatInput"] textarea,
div[data-testid="stTextInput"] input {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    font-family: 'Inter', sans-serif !important;
}

div[data-testid="stChatInput"] textarea::placeholder,
div[data-testid="stChatInput"] textarea::-webkit-input-placeholder,
div[data-testid="stChatInput"] textarea::-moz-placeholder,
div[data-testid="stChatInput"] textarea:-ms-input-placeholder,
div[data-testid="stTextInput"] input::placeholder,
div[data-testid="stTextInput"] input::-webkit-input-placeholder,
div[data-testid="stTextInput"] input::-moz-placeholder,
div[data-testid="stTextInput"] input:-ms-input-placeholder {
    color: rgba(255, 255, 255, 0.6) !important;
    -webkit-text-fill-color: rgba(255, 255, 255, 0.6) !important;
    opacity: 1 !important;
}

.approval-box {
    background: linear-gradient(135deg, rgba(30, 27, 75, 0.85) 0%, rgba(15, 23, 42, 0.95) 100%);
    border: 1px solid rgba(245, 158, 11, 0.4);
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 0 25px rgba(245, 158, 11, 0.15);
    animation: fadeInUp 0.4s ease-out, pulseAmber 3s infinite;
    margin-top: 1rem;
    margin-bottom: 1.5rem;
}

.stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    background: rgba(30, 41, 59, 0.8) !important;
    color: #F1F5F9 !important;
    transition: all 0.2s ease-in-out !important;
}

.stButton > button:hover {
    background: rgba(51, 65, 85, 0.9) !important;
    border-color: rgba(6, 182, 212, 0.4) !important;
    color: #FFFFFF !important;
    transform: translateY(-1px) !important;
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #06B6D4 0%, #2563EB 100%) !important;
    color: #FFFFFF !important;
    border: none !important;
    box-shadow: 0 4px 14px rgba(6, 182, 212, 0.3) !important;
}

.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #0891B2 0%, #1D4ED8 100%) !important;
    box-shadow: 0 6px 20px rgba(6, 182, 212, 0.45) !important;
    transform: translateY(-1px) !important;
}

code {
    color: #38BDF8 !important;
    background-color: rgba(15, 23, 42, 0.8) !important;
    border: 1px solid rgba(56, 189, 248, 0.2) !important;
    border-radius: 6px !important;
    padding: 2px 6px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.85em !important;
}

div[data-testid="stCodeBlock"] pre {
    background-color: #0F172A !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 8px !important;
    font-family: 'JetBrains Mono', monospace !important;
}

div[data-testid="stForm"], div[data-testid="stBorderedContainer"] {
    background: rgba(19, 27, 46, 0.7) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 12px !important;
    padding: 1.5rem !important;
    backdrop-filter: blur(10px) !important;
}

.stMarkdown, p {
    color: #CBD5E1;
}

.stCaption {
    color: #94A3B8 !important;
}

/* ── Chat History Popover & Expander — DARK THEME ── */
button[data-testid="stPopoverButton"] {
    background: rgba(19, 27, 46, 0.85) !important;
    border: 1px solid rgba(6, 182, 212, 0.3) !important;
    color: #E2E8F0 !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    width: 100% !important;
    transition: all 0.2s ease !important;
}
button[data-testid="stPopoverButton"]:hover {
    background: rgba(30, 41, 59, 0.95) !important;
    border-color: #06B6D4 !important;
    color: #38BDF8 !important;
}
div[data-testid="stPopover"] > div {
    background: #0F172A !important;
    border: 1px solid rgba(6, 182, 212, 0.25) !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5) !important;
    border-radius: 12px !important;
    color: #F1F5F9 !important;
}
div[data-testid="stPopover"] p,
div[data-testid="stPopover"] span,
div[data-testid="stPopover"] label {
    color: #CBD5E1 !important;
}
div[data-testid="stExpander"] {
    background: rgba(19, 27, 46, 0.7) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 10px !important;
}
div[data-testid="stExpander"] summary {
    color: #E2E8F0 !important;
    font-weight: 600 !important;
}
div[data-testid="stExpander"] > div > div {
    background: rgba(15, 23, 42, 0.85) !important;
    color: #CBD5E1 !important;
}
</style>
"""

# Inject Dynamic CSS based on session_state
st.markdown(get_theme_css(st.session_state.theme), unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  TOP HEADER & LIVE METRICS BAR
# ─────────────────────────────────────────────
with st.container():
    ist_tz = timezone(timedelta(hours=5, minutes=30))
    now_str = datetime.now(ist_tz).strftime("%H:%M IST")
    
    col_head_main, col_head_side = st.columns([3, 1])
    with col_head_side:
        # Theme Toggle Switch Widget
        is_dark_selected = st.toggle(
            "🌙 Dark Theme" if st.session_state.theme == "dark" else "☀️ Light Theme",
            value=(st.session_state.theme == "dark"),
            key="theme_toggle_switch",
        )
        new_theme = "dark" if is_dark_selected else "light"
        if new_theme != st.session_state.theme:
            st.session_state.theme = new_theme
            st.rerun()

    with col_head_main:
        sub_text_color = "#94A3B8" if st.session_state.theme == "dark" else "#64748B"
        st.markdown(
            f"""
            <div class="console-header-card">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                    <div>
                        <h1 class="console-title">
                            🛡️ SecureOps AI <span class="title-accent">Console</span>
                        </h1>
                        <div style="font-size: 13px; font-weight: 500; margin-top: 2px; color: {sub_text_color} !important;">
                            Autonomous Security Operations & Multi-Domain Threat Correlation
                        </div>
                    </div>
                    <div style="text-align: right; padding: 6px 14px; border-radius: 20px; border: 1px solid rgba(150, 150, 150, 0.2);">
                        <span class="status-dot-online"></span>
                        <span style="color: #10B981 !important; font-weight: 600; font-size: 13px;">Live Engine</span>
                        <span style="margin: 0 6px; opacity: 0.5;">|</span>
                        <span style="font-size: 13px; font-weight: 500;">{now_str}</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# 4-Column Live Metric Stats Bar
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
    st.markdown(
        """
        <div class="metric-card">
            <div class="metric-label">SOC Engine Status</div>
            <div class="metric-value" style="color: #10B981;">🟢 Active</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col_m2:
    st.markdown(
        """
        <div class="metric-card">
            <div class="metric-label">Specialist Agents</div>
            <div class="metric-value" style="color: #38BDF8;">6 Subagents</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col_m3:
    st.markdown(
        """
        <div class="metric-card">
            <div class="metric-label">Security Posture</div>
            <div class="metric-value" style="color: #F59E0B;">⚡ Monitoring</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col_m4:
    # ── Chat History Popover (ChatGPT/Gemini-style) ──
    history = st.session_state.chat_history
    history_count = len(history)
    _popover_label = f"🕒 History ({history_count})" if history_count else "🕒 History"

    # Use st.popover if available (Streamlit ≥ 1.31), else fall back to expander
    _use_popover = hasattr(st, "popover")
    _ctx = st.popover(_popover_label) if _use_popover else st.expander(_popover_label)

    with _ctx:
        # ── New Chat button ──
        if st.button("➕  New Chat", use_container_width=True, key="new_chat_btn"):
            st.session_state.thread_id = str(uuid.uuid4())
            st.session_state.current_chat_id = None
            st.rerun()

        if history:
            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
            if st.button("🗑️  Clear All History", use_container_width=True, key="clear_history_btn", type="primary"):
                save_chat_history({})
                st.session_state.chat_history = {}
                st.session_state.thread_id = str(uuid.uuid4())
                st.session_state.current_chat_id = None
                st.toast("All chat history cleared.", icon="🗑️")
                st.rerun()

            st.markdown("---")
            st.caption("Previous Sessions")
            sorted_chats = sorted(
                history.items(),
                key=lambda kv: kv[1].get("created_at", ""),
                reverse=True,
            )
            for chat_id, meta in sorted_chats:
                btn_label = meta.get("title", chat_id[:12] + "…")
                is_active = (chat_id == st.session_state.current_chat_id)
                label_display = f"▶ {btn_label}" if is_active else btn_label
                if st.button(
                    label_display,
                    key=f"hist_{chat_id}",
                    use_container_width=True,
                ):
                    st.session_state.thread_id = meta["thread_id"]
                    st.session_state.current_chat_id = chat_id
                    st.rerun()
        else:
            st.caption("No previous sessions yet.")

st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  STATE FETCHING (Executed before rendering UI)
# ─────────────────────────────────────────────
current_state = supervisor_graph.get_state(config)
messages_in_graph = current_state.values.get("messages", [])
is_paused = len(current_state.next) > 0

# Check human approval requirement
requires_approval = False
if is_paused:
    last_message = current_state.values["messages"][-1]
    pending_tools = (
        [tc["name"] for tc in last_message.tool_calls]
        if hasattr(last_message, "tool_calls")
        else []
    )
    sensitive_tools = ["incident_specialist"]
    requires_approval = any(t in sensitive_tools for t in pending_tools)

# ─────────────────────────────────────────────
#  SECURITY OPERATIONS CONSOLE
# ─────────────────────────────────────────────
# Quick Action Prompt Chips
st.markdown("<div style='color: #94A3B8; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px;'>⚡ Quick Threat Queries</div>", unsafe_allow_html=True)

col_chip1, col_chip2, col_chip3, col_chip4 = st.columns(4)
with col_chip1:
    if st.button("🚨 Critical SIEM Alerts", use_container_width=True):
        st.session_state.preset_prompt = "Check critical SIEM alerts and analyze severity"
with col_chip2:
    if st.button("💻 Host Endpoint Status", use_container_width=True):
        st.session_state.preset_prompt = "Check device health and malware status for host-01"
with col_chip3:
    if st.button("🔑 Identity Anomalies", use_container_width=True):
        st.session_state.preset_prompt = "Audit login history and anomalous activity for user dev-01"
with col_chip4:
    if st.button("🕵️ Correlate Threat Hunt", use_container_width=True):
        st.session_state.preset_prompt = "Run threat hunting correlation on recent suspicious activity"

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

# 1. RENDER CHAT HISTORY FIRST
with st.container():
    if not messages_in_graph:
        st.info("💡 **Session Ready**: Select a quick query above or enter a custom prompt below to begin security operations telemetry.")
    
    for msg in messages_in_graph:
        if isinstance(msg, HumanMessage) and msg.content:
            with st.chat_message("user"):
                st.markdown(str(msg.content))
        elif isinstance(msg, AIMessage) and msg.content:
            with st.chat_message("assistant"):
                st.markdown(str(msg.content))

# ─────────────────────────────────────────────
#  BOTTOM ACTIONS & SPINNERS (Fixes Scroll Anchor)
# ─────────────────────────────────────────────

# 2. AUTO-EXECUTE NON-SENSITIVE TOOLS
if is_paused and not requires_approval:
    with st.chat_message("assistant"):
        with st.spinner("Processing telemetry request..."):
            supervisor_graph.invoke(None, config)
            st.rerun()

# 3. HUMAN-IN-THE-LOOP APPROVAL GATE
elif is_paused and requires_approval:
    st.markdown(
        """
        <div class="approval-box">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                <span style="font-size: 20px;">⚠️</span>
                <h3 style="margin: 0; color: #F59E0B; font-size: 18px; font-weight: 700;">Human Authorization Required</h3>
            </div>
            <p style="color: #CBD5E1; font-size: 13px; margin-bottom: 16px;">
                The assistant has requested to execute a sensitive operation modifying production incident records. Review payload details below:
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for tc in last_message.tool_calls:
        try:
            args_pretty = json.dumps(tc["args"], indent=2)
        except Exception:
            args_pretty = str(tc["args"])

        col_a, col_b = st.columns([1, 2])
        with col_a:
            st.markdown(f"**Target Agent / Tool**\n`{tc['name']}`")
        with col_b:
            st.markdown("**Action Payload**")
            st.code(args_pretty, language="json")

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Approve & Execute Action", type="primary", use_container_width=True):
            with st.chat_message("assistant"):
                with st.spinner("Executing approved action..."):
                    supervisor_graph.invoke(None, config)
            st.toast("Action authorized & executed.", icon="✅")
            st.rerun()
    with col2:
        if st.button("🛑 Reject Request", use_container_width=True):
            rejection_payload = json.dumps({
                "status": "blocked",
                "error": "ACTION REJECTED: Security analyst explicitly blocked this operation."
            })
            tool_msgs = [
                ToolMessage(
                    content=rejection_payload,
                    tool_call_id=tc["id"],
                    name=tc["name"],
                )
                for tc in last_message.tool_calls
            ]
            supervisor_graph.update_state(
                config, {"messages": tool_msgs}, as_node="tools"
            )
            with st.chat_message("assistant"):
                with st.spinner("Notifying AI Supervisor of rejection..."):
                    supervisor_graph.invoke(None, config)
            st.toast("Request rejected and aborted.", icon="✋")
            st.rerun()

# 4. ACTIVE PROMPT EXECUTION
active_prompt = None

if st.session_state.preset_prompt:
    active_prompt = st.session_state.preset_prompt
    st.session_state.preset_prompt = None

if not is_paused:
    user_input = st.chat_input("Enter security query or command...")
    if user_input:
        active_prompt = user_input

if active_prompt and not is_paused:
    with st.chat_message("user"):
        st.markdown(active_prompt)

    # Auto-name & persist this chat on the FIRST message
    if st.session_state.current_chat_id is None:
        new_chat_id = str(uuid.uuid4())
        st.session_state.current_chat_id = new_chat_id
        st.session_state.chat_history[new_chat_id] = {
            "title": auto_title(active_prompt),
            "thread_id": st.session_state.thread_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        save_chat_history(st.session_state.chat_history)

    # Wrap the spinner in an assistant message so Streamlit scrolls down to it
    with st.chat_message("assistant"):
        with st.spinner("Orchestrating threat telemetry subagents..."):
            try:
                supervisor_graph.invoke(
                    {"messages": [HumanMessage(content=active_prompt)]}, config
                )
                st.rerun()
            except Exception as e:
                st.error(f"Execution error: {str(e)}")