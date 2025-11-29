"""
Utilidades para analizar la ejecución de agentes
"""
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import MessageRole, ListSortOrder
from typing import Dict


def analyze_run_steps(
        agents_client: AgentsClient,
        thread_id: str,
        run_id: str,
        mcp_agent_id: str,
        knowledge_base_agent_id: str,
) -> Dict[str, bool]:
    """
    Analiza los pasos de ejecución y retorna qué herramientas se usaron
    """
    print(f'\n{"=" * 80}')
    print("ANÁLISIS DE STEPS")
    print(f'{"=" * 80}')

    tools_called = {
        "policy_guard": True,
        "mcp_ado": False,
        "knowledge_base": False,
    }

    run_steps = agents_client.run_steps.list(
        thread_id=thread_id,
        run_id=run_id,
    )

    for idx, step in enumerate(run_steps, 1):
        print(f"\n┌─ Step {idx}")
        print(f"│  Type: {step.type}")
        print(f"│  Status: {step.status}")

        if hasattr(step, "step_details") and step.step_details:
            if hasattr(step.step_details, "tool_calls") and step.step_details.tool_calls:
                for tool_call in step.step_details.tool_calls:
                    print(f"│  🔧 Tool type: {tool_call.type}")

                    if hasattr(tool_call, "function") and tool_call.function:
                        print(f"│     Function: {tool_call.function.name}")

                    if hasattr(tool_call, "agent") and tool_call.agent:
                        agent_id = tool_call.agent.agent_id
                        print(f"│     Agent ID: {agent_id}")

                        if agent_id == mcp_agent_id:
                            print("│  ⚙️ MCP ADO llamado")
                            tools_called["mcp_ado"] = True

                            if hasattr(tool_call.agent, "output"):
                                output = tool_call.agent.output
                                if "✅" in output and "EXITOSAMENTE" in output:
                                    print("│     ✅ Ejecución exitosa")
                                elif "❌" in output:
                                    print("│     ❌ Ejecución fallida")

                        elif agent_id == knowledge_base_agent_id:
                            print("│  📚 Knowledge Base llamado")
                            tools_called["knowledge_base"] = True

    return tools_called


def get_final_response(agents_client: AgentsClient, thread_id: str) -> str:
    """Obtiene la respuesta final del agente"""
    print(f'\n{"=" * 80}')
    print("RESPUESTA FINAL")
    print(f'{"=" * 80}')

    messages = agents_client.messages.list(
        thread_id=thread_id,
        order=ListSortOrder.DESCENDING,
    )

    last_message = next(
        (m for m in messages if m.role == MessageRole.AGENT and m.text_messages),
        None,
    )

    response_text = ""
    if last_message:
        response_text = last_message.text_messages[-1].text.value
        print(response_text)
    else:
        print("⚠️ No hay respuesta")

    return response_text
