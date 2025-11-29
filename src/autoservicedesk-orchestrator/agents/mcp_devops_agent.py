from azure.ai.agents.models import ConnectedAgentTool, McpTool

def create_mcp_devops_agent(agents_client, model_deployment: str, mcp_server_url: str):
    mcp_server_label = "external_tools"
    mcp_tool = McpTool(
        server_label=mcp_server_label,
        server_url=mcp_server_url,
    )
    mcp_tool.set_approval_mode("never")

    mcp_agent_name = "mcp_research_agent"
    mcp_agent_instructions = """
    You are the Azure DevOps MCP Client Agent with access to Azure DevOps via MCP tools.

    YOU CAN:
    - Grant repository permissions (Contributor, Reader, etc.)
    - Create work items
    - Modify branch policies
    - Manage project access
    - Query repository information
    
    INPUT: JSON with clear action details:
    {
      "action": "grant_permission" | "create_work_item" | "modify_policy" | ...,
      "user_email": "target@company.com",
      "repository": "repo-name",
      "project": "project-name",
      "permission_level": "Contributor" | "Reader" | ...,
      "work_item_details": {...} // if creating work item
    }
    
    YOUR TASK:
    1. Identify the appropriate MCP tool for the action
    2. Call the tool with correct parameters
    3. Verify the result
    4. Format response clearly
    
    OUTPUT FORMAT:
    Always start with status indicator:
    ✅ PERMISO ASIGNADO EXITOSAMENTE
    or
    ❌ ERROR AL EJECUTAR LA OPERACIÓN
    
    Then provide details:
    👤 Usuario: [name] ([email])
    📦 Repositorio: [repo]
    🔐 Permiso: [level]
    [additional relevant details]
    
    RULES:
    - Always verify parameters before calling tools
    - Provide clear error messages if tool fails
    - Include relevant IDs (project_id, repo_id, etc.) in output
    - There is no need to ask for the project to the user because the only one available is Hackathon2025.
    
    """

    agent = agents_client.create_agent(
        model=model_deployment,
        name=mcp_agent_name,
        instructions=mcp_agent_instructions,
        tools=mcp_tool.definitions,
    )

    tool = ConnectedAgentTool(
        id=agent.id,
        name=mcp_agent_name,
        description=(
            "Executes actions in Azure DevOps using MCP tools. "
            "Use for: granting repository permissions, creating work items, "
            "modifying branch policies, managing projects. "
            "Call ONLY when: (1) policy_guard_agent returned AUTO_APPROVE, "
            "OR (2) user confirmed they want a work item created. "
            "Input: Clear structured JSON with action, target_user, repository, "
            "project, permission_level, or work_item details. "
            "Output: Text indicating success/failure with details. "
            "Success indicators: '✅', 'EXITOSAMENTE', 'PERMISO ASIGNADO'."
        ),
    )

    # También devolvemos el McpTool para el ToolSet del run
    return agent, tool, mcp_tool