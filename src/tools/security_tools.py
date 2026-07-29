import json
from langchain_core.tools import tool

# ── Known mock entities ──────────────────────────────────────────────────────
# Only these entities exist in the simulated environment.
# Any other input returns a "not found" response to prevent hallucination.
KNOWN_USERS = {"admin", "jdoe", "dev-01", "dev01"}
KNOWN_HOSTS = {"host-01", "host-12", "host-44", "host01"}
KNOWN_ALERTS = {"alt-101", "alt-102"}

# --- 1. Alert Tools ---
@tool
def search_alerts(query: str) -> str:
    """Searches security alerts in the SIEM platform."""
    mock_data = {
        "alerts": [
            {"id": "ALT-101", "type": "Unauthorized API Access", "severity": "High", "source_ip": "198.51.100.45"},
            {"id": "ALT-102", "type": "Multiple Failed Logins", "severity": "Medium", "source_ip": "192.168.1.105"}
        ]
    }
    return json.dumps(mock_data)

@tool
def check_alert_severity(alert_id: str) -> str:
    """Checks the severity level and detailed metadata of a specific alert."""
    if alert_id.lower() not in KNOWN_ALERTS:
        return json.dumps({"found": False, "alert_id": alert_id, "message": f"No alert with ID '{alert_id}' exists in the SIEM."})
    mock_data = {"alert_id": alert_id, "severity": "Critical", "score": 8.9, "status": "Open"}
    return json.dumps(mock_data)

# --- 2. Endpoint Tools ---
@tool
def check_device_status(hostname: str) -> str:
    """Checks device health, OS version, and isolation/quarantine status."""
    if hostname.lower() not in KNOWN_HOSTS:
        return json.dumps({"found": False, "hostname": hostname, "message": f"No device named '{hostname}' was found in the asset inventory."})
    mock_data = {"hostname": hostname, "status": "Quarantined", "health": "At Risk", "os": "Windows 11 Enterprise"}
    return json.dumps(mock_data)

@tool
def review_malware_detection(hostname: str) -> str:
    """Fetches recent malware detection events for a target device."""
    if hostname.lower() not in KNOWN_HOSTS:
        return json.dumps({"found": False, "hostname": hostname, "message": f"No malware detection records found for '{hostname}'."})
    mock_data = {"hostname": hostname, "malware_found": "Trojan.Win32.Generic", "action_taken": "File Quarantined"}
    return json.dumps(mock_data)

# --- 3. Identity Tools ---
@tool
def check_login_history(username: str) -> str:
    """Retrieves recent login activity and authentication events for a user."""
    if username.lower().replace(" ", "-").replace(" ", "") not in KNOWN_USERS and username.lower() not in KNOWN_USERS:
        return json.dumps({"found": False, "user": username, "message": f"No user named '{username}' exists in the Identity Provider. No login records found."})
    mock_data = {
        "user": username,
        "logins": [
            {"timestamp": "2026-07-25T10:00:00Z", "location": "New York, USA", "status": "Failed"},
            {"timestamp": "2026-07-25T10:05:00Z", "location": "London, UK", "status": "Success"}
        ]
    }
    return json.dumps(mock_data)

@tool
def search_user_activity(username: str) -> str:
    """Searches privileged activity and resource access history for a user."""
    if username.lower().replace(" ", "-").replace(" ", "") not in KNOWN_USERS and username.lower() not in KNOWN_USERS:
        return json.dumps({"found": False, "user": username, "message": f"No user named '{username}' exists in the system. No activity records found."})
    mock_data = {"user": username, "accessed_resources": ["S3://prod-db-backups", "IAM:GrantRole"], "anomalous": True}
    return json.dumps(mock_data)

# --- 4. Incident Tools ---
@tool
def create_security_incident(title: str, severity: str) -> str:
    """Creates a new incident record in the Incident Management System."""
    mock_data = {"incident_id": "INC-9901", "title": title, "severity": severity, "status": "Created"}
    return json.dumps(mock_data)

@tool
def escalate_incident(incident_id: str, reason: str) -> str:
    """Escalates an existing incident to Tier 2/3 SOC analysts."""
    mock_data = {"incident_id": incident_id, "escalated": True, "reason": reason}
    return json.dumps(mock_data)

# --- 5. Reporting Tools ---
@tool
def generate_investigation_report(incident_id: str) -> str:
    """Generates an executive summary and timeline report for an investigation."""
    mock_data = {
        "incident_id": incident_id,
        "summary": "Multi-stage attack involving credential access followed by lateral movement.",
        "timeline": ["10:00 - Failed logins", "10:05 - Successful login from abroad", "10:12 - Malware detected"]
    }
    return json.dumps(mock_data)


# Grouped tool lists exported for indexing in subagents.py
alert_tools = [search_alerts, check_alert_severity]
endpoint_tools = [check_device_status, review_malware_detection]
identity_tools = [check_login_history, search_user_activity]
incident_tools = [create_security_incident, escalate_incident]
reporting_tools = [generate_investigation_report]

# --- 6. Threat Hunting Tools ---
@tool
def query_security_data_lake(query: str) -> str:
    """Queries the centralized security data lake for multi-domain event correlation and threat hunting."""
    mock_scenarios = {
        "impossible_travel": {
            "events": [
                {"time": "08:00Z", "source": "Identity", "event": "5 Failed logins for user admin"},
                {"time": "08:15Z", "source": "Identity", "event": "Successful login for user admin from IP 203.0.113.5 (Russia)"}
            ],
            "risk_score": 9.2,
            "correlation_reasoning": "Multiple failed authentication attempts immediately followed by a successful login from a geographically distant, anomalous location indicates likely credential compromise.",
            "recommendation": "Suspend user 'admin', revoke session tokens, and initiate incident response for compromised identity."
        },
        "ransomware_prep": {
            "events": [
                {"time": "14:00Z", "source": "Endpoint", "event": "Low severity: Suspicious powershell script executed on HOST-12"},
                {"time": "14:30Z", "source": "Endpoint", "event": "Low severity: Volume Shadow Copy deletion attempt blocked"},
                {"time": "14:45Z", "source": "Network", "event": "Medium severity: Unusual outbound traffic to known Tor exit node"}
            ],
            "risk_score": 9.5,
            "correlation_reasoning": "Sequential low-severity alerts on the same endpoint (script execution, backup tampering, C2 communication) strongly indicate early-stage ransomware deployment.",
            "recommendation": "Isolate HOST-12 immediately, block destination IP on firewall, and escalate to Tier 3."
        },
        "malware_c2": {
            "events": [
                {"time": "11:10Z", "source": "Endpoint", "event": "Trojan.Win32.Generic detected and quarantined on HOST-44"},
                {"time": "11:15Z", "source": "Firewall", "event": "Unusual sustained outbound connection over port 443 from HOST-44 to IP 198.51.100.99"}
            ],
            "risk_score": 8.8,
            "correlation_reasoning": "Malware detection followed by anomalous outbound traffic from the same host suggests the initial malware may have successfully established a Command & Control channel before quarantine.",
            "recommendation": "Isolate HOST-44, block IP 198.51.100.99, and run full AV scan on all adjacent network endpoints."
        },
        "insider_threat": {
            "events": [
                {"time": "23:45Z", "source": "Identity", "event": "User jdoe accessed production DB outside business hours"},
                {"time": "23:55Z", "source": "DLP", "event": "Large outbound file transfer (5GB) initiated by jdoe"}
            ],
            "risk_score": 8.5,
            "correlation_reasoning": "Off-hours privileged access combined with massive data exfiltration points to potential insider threat or compromised account exfiltrating data.",
            "recommendation": "Temporarily suspend user 'jdoe', terminate active DB connections, and block outbound transfer."
        },
        "cloud_compromise": {
            "events": [
                {"time": "09:00Z", "source": "AWS CloudTrail", "event": "IAM policy modified: Admin privileges granted to temp-role-1"},
                {"time": "09:05Z", "source": "AWS CloudTrail", "event": "Multiple EC2 instances terminated by temp-role-1"}
            ],
            "risk_score": 9.8,
            "correlation_reasoning": "Privilege escalation via IAM policy modification immediately followed by destructive API calls represents a critical cloud infrastructure compromise.",
            "recommendation": "Revoke 'temp-role-1' IAM permissions immediately, pause further EC2 terminations via SCP, and page cloud on-call."
        }
    }
    
    query_lower = query.lower()
    if "login" in query_lower or "travel" in query_lower or "admin" in query_lower:
        return json.dumps(mock_scenarios["impossible_travel"])
    elif "ransomware" in query_lower or "powershell" in query_lower:
        return json.dumps(mock_scenarios["ransomware_prep"])
    elif "malware" in query_lower or "outbound" in query_lower:
        return json.dumps(mock_scenarios["malware_c2"])
    elif "insider" in query_lower or "transfer" in query_lower or "jdoe" in query_lower:
        return json.dumps(mock_scenarios["insider_threat"])
    elif "cloud" in query_lower or "iam" in query_lower or "ec2" in query_lower:
        return json.dumps(mock_scenarios["cloud_compromise"])
    else:
        return json.dumps({
            "status": "No specific scenario matched",
            "message": "Query did not match a known threat pattern. Please refine your query.",
            "available_scenario_types": [
                "impossible_travel — credential compromise via geo-impossible logins",
                "ransomware_prep — multi-stage ransomware indicators on endpoint",
                "malware_c2 — malware establishing C2 channel post-quarantine",
                "insider_threat — off-hours privileged access with data exfiltration",
                "cloud_compromise — IAM escalation followed by destructive cloud API calls"
            ]
        })

threat_hunting_tools = [query_security_data_lake]