from azure.ai.agents.models import ConnectedAgentTool

def create_knowledge_base_tool(agent_id: str) -> ConnectedAgentTool:
    """
    Knowledge Base RAG: Responde preguntas usando manuales internos
    mediante RAG sobre documentación de procedimientos.
    """
    return ConnectedAgentTool(
        id=agent_id,
        name="knowledge_base_rag",
        description=(
            "Answers questions about company procedures, installation guides, "
            "and internal documentation using RAG over knowledge base. "
            "Use for: 'how to' questions, 'what is' questions, explanations "
            "of policies or procedures. "
            "Do NOT use for permission requests - those go to policy_guard_agent. "
            "Input: JSON with question and optional user_context (role, area). "
            "Output: Detailed answer based on internal documentation with "
            "citations to source documents."
        ),
    )
