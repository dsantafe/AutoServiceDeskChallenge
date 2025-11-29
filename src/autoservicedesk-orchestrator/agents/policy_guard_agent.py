from azure.ai.agents.models import ConnectedAgentTool

def create_policy_guard_tool(policy_agent_id: str):
    tool = ConnectedAgentTool(
        id=policy_agent_id,
        name="policy_guard_agent",
        description=(
            "Validates user permissions against company security policies using RAG. "
            "Call this ONLY for ACCESS REQUESTS or PERMISSION CHANGES, never for questions. "
            "Input: JSON with user_request, user_email, user_profile, action, resource. "
            "Output: JSON with decision (AUTO_APPROVE/REQUIRES_APPROVAL/DENIED), "
            "risk_level, reason, policy_refs, and required_approver_role if applicable. "
            "Do NOT call if cached_policy_decision is provided in input."
        ),
    )
    return tool
