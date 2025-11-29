"""
Orquestador principal del sistema multiagente
"""
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import MessageRole, ToolSet
from azure.identity import DefaultAzureCredential
import json
from typing import Dict, Optional

import config
import context
from policy import call_policy_guard
from agents_utils import interpret_confirmation, generate_ux_message, create_triage_agent
from run_utils import analyze_run_steps, get_final_response
from services.user_profile import get_user_profile
from agents.mcp_devops_agent import create_mcp_devops_agent
from agents.knowledge_base_agent import create_knowledge_base_tool


def create_agents_client() -> AgentsClient:
    """Crea el cliente de Azure AI Agents"""
    return AgentsClient(
        endpoint=config.PROJECT_ENDPOINT,
        credential=DefaultAzureCredential(
            exclude_environment_credential=True,
            exclude_managed_identity_credential=True,
        ),
    )


def handle_confirmation_flow(
        agents_client: AgentsClient,
        user_request: str,
        user_email: str,
        thread_id: str,
) -> Dict:
    """Maneja el flujo cuando estamos esperando confirmación del usuario"""

    conv_context = context.get_context(thread_id)

    # Interpretar respuesta del usuario
    decision = interpret_confirmation(
        agents_client,
        config.MODEL_DEPLOYMENT_NAME,
        user_request
    )
    print(f"🤖 Interpretación confirmación: {decision}")

    tools_called = {
        "policy_guard": True,
        "mcp_ado": False,
        "knowledge_base": False,
    }

    # Usuario dijo NO
    if decision == "no":
        context.clear_confirmation_flag(thread_id)

        state = {
            "mode": "INFO",
            "policy_decision": conv_context.get("last_policy_decision"),
            "extra_context": {
                "reason": "Usuario rechazó la creación del ticket de aprobación.",
            },
        }
        response_text = generate_ux_message(
            agents_client,
            config.MODEL_DEPLOYMENT_NAME,
            state
        )

        return {
            "thread_id": thread_id,
            "response": response_text,
            "tools_used": tools_called,
            "run_status": "completed",
        }

    # Usuario dijo SÍ
    if decision == "yes":
        original_request = conv_context.get("last_denied_request") or user_request
        user_profile = get_user_profile(user_email)
        last_policy_decision = conv_context.get("last_policy_decision")

        print("✅ Usuario confirmó creación de ticket, llamando al multiagente...")

        return execute_multiagent_flow(
            agents_client,
            original_request,
            user_email,
            user_profile,
            thread_id,
            conv_context,
            last_policy_decision,
            mode="CREATE_APPROVAL_TICKET",
        )

    # No está claro
    state = {
        "mode": "ASK_CONFIRMATION_AGAIN",
        "policy_decision": conv_context.get("last_policy_decision"),
        "extra_context": {
            "instruction": "El usuario no fue claro, pídele que responda solo sí o no.",
        },
    }
    response_text = generate_ux_message(
        agents_client,
        config.MODEL_DEPLOYMENT_NAME,
        state
    )

    return {
        "thread_id": thread_id,
        "response": response_text,
        "tools_used": tools_called,
        "run_status": "waiting_confirmation",
    }


def execute_multiagent_flow(
        agents_client: AgentsClient,
        user_request: str,
        user_email: str,
        user_profile: Dict,
        thread_id: Optional[str],
        conv_context: Dict,
        policy_decision: Dict,
        mode: Optional[str] = None,
) -> Dict:
    """Ejecuta el flujo completo multiagente (Triage + MCP + Knowledge)"""

    # Crear agentes dinámicos
    mcp_agent, mcp_agent_tool, mcp_tool = create_mcp_devops_agent(
        agents_client,
        config.MODEL_DEPLOYMENT_NAME,
        config.MCP_SERVER_URL
    )
    print(f"✅ MCP Agent creado: {mcp_agent.id}")

    knowledge_base_tool = create_knowledge_base_tool(config.KNOWLEDGE_BASE_AGENT_ID)

    triage_agent = create_triage_agent(
        agents_client,
        config.MODEL_DEPLOYMENT_NAME,
        [knowledge_base_tool.definitions[0], mcp_agent_tool.definitions[0]],
    )

    # Asegurar thread
    if thread_id is None:
        thread = agents_client.threads.create()
        thread_id = thread.id
        print(f"✨ Nuevo thread: {thread_id}")
    else:
        print(f"♻️ Reutilizando thread: {thread_id}")

    # Preparar payload
    payload = {
        "user_request": user_request,
        "user_email": user_email,
        "user_profile": user_profile,
        "conversation_state": conv_context,
        "policy_decision": policy_decision,
    }

    if mode:
        payload["mode"] = mode

    print(f"\n📤 Payload:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    # Ejecutar
    agents_client.messages.create(
        thread_id=thread_id,
        role=MessageRole.USER,
        content=json.dumps(payload, ensure_ascii=False),
    )

    toolset = ToolSet()
    toolset.add(mcp_tool)

    run = agents_client.runs.create_and_process(
        thread_id=thread_id,
        agent_id=triage_agent.id,
        #toolset=toolset,
    )

    # Analizar resultados
    tools_called = analyze_run_steps(
        agents_client,
        thread_id,
        run.id,
        mcp_agent.id,
        config.KNOWLEDGE_BASE_AGENT_ID,
    )

    response_text = get_final_response(agents_client, thread_id)

    # Limpieza
    print(f'\n{"=" * 80}')
    print("LIMPIEZA")
    print(f'{"=" * 80}')
    agents_client.delete_agent(triage_agent.id)
    agents_client.delete_agent(mcp_agent.id)
    print("✅ Agentes temporales eliminados")

    if mode == "CREATE_APPROVAL_TICKET":
        context.clear_confirmation_flag(thread_id)

    return {
        "thread_id": thread_id,
        "response": response_text,
        "tools_used": tools_called,
        "run_status": run.status,
    }


def handle_policy_decision(
        agents_client: AgentsClient,
        decision: Dict,
        user_request: str,
        thread_id: str,
) -> Optional[Dict]:
    """
    Maneja las diferentes decisiones del Policy Guard.
    Retorna None si debe continuar con el multiagente.
    """
    decision_value = decision.get("decision", "").upper()

    tools_called = {
        "policy_guard": True,
        "mcp_ado": False,
        "knowledge_base": False,
    }

    # REQUIERE APROBACIÓN
    if decision_value == "REQUIERE_APROBACION":
        context.set_waiting_confirmation(thread_id, user_request, decision)

        state = {
            "mode": "NEEDS_APPROVAL",
            "policy_decision": decision,
            "extra_context": {
                "instruction": (
                    "Explica brevemente que la acción requiere aprobación previa y "
                    "pregunta al usuario si desea que se cree un ticket de aprobación "
                    "en Azure DevOps. Pídele que responda sí o no."
                ),
            },
        }
        response_text = generate_ux_message(
            agents_client,
            config.MODEL_DEPLOYMENT_NAME,
            state
        )

        return {
            "thread_id": thread_id,
            "response": response_text,
            "tools_used": tools_called,
            "run_status": "needs_approval",
        }

    # DENEGAR
    if decision_value == "DENEGAR":
        state = {
            "mode": "DENIED",
            "policy_decision": decision,
        }
        response_text = generate_ux_message(
            agents_client,
            config.MODEL_DEPLOYMENT_NAME,
            state
        )

        return {
            "thread_id": thread_id,
            "response": response_text,
            "tools_used": tools_called,
            "run_status": "denied",
        }

    # AUTO_APROBAR -> continuar
    return None


def process_request(
        user_request: str,
        user_email: str,
        thread_id: Optional[str] = None,
) -> Dict:
    """
    Función principal que procesa una solicitud del usuario.

    Flujo:
    1. Si hay thread con confirmación pendiente -> manejar confirmación
    2. Si no, evaluar con Policy Guard
    3. Según decisión:
       - REQUIERE_APROBACION -> preguntar
       - DENEGAR -> denegar
       - AUTO_APROBAR -> ejecutar multiagente
    """
    agents_client = create_agents_client()

    with agents_client:
        # 1) Verificar si estamos esperando confirmación
        if thread_id is not None:
            conv_context = context.get_context(thread_id)

            if conv_context.get("awaiting_work_item_confirmation", False):
                return handle_confirmation_flow(
                    agents_client,
                    user_request,
                    user_email,
                    thread_id,
                )

        # 2) Flujo normal: Policy Guard primero
        user_profile = get_user_profile(user_email)
        print("🔍 Llamando a Policy Guard antes del multiagente...")

        policy_result = call_policy_guard(
            agents_client,
            config.POLICY_AGENT_ID,
            user_request,
            user_email,
            user_profile,
            thread_id,
        )

        thread_id = policy_result["thread_id"]
        decision = policy_result["decision"]

        # Actualizar contexto
        conv_context = context.get_context(thread_id)
        conv_context["last_policy_decision"] = decision
        context.update_context(thread_id, conv_context)

        # 3) Manejar decisión de política
        policy_response = handle_policy_decision(
            agents_client,
            decision,
            user_request,
            thread_id,
        )

        if policy_response:
            return policy_response

        # 4) Auto-aprobado: ejecutar multiagente
        print("✅ Policy Guard permite continuar, llamando al orquestador multiagente...")

        return execute_multiagent_flow(
            agents_client,
            user_request,
            user_email,
            user_profile,
            thread_id,
            conv_context,
            decision,
        )
