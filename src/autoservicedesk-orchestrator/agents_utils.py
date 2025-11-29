"""
Funciones auxiliares para agentes
"""
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import MessageRole, ListSortOrder
import json
from typing import Dict


def interpret_confirmation(agents_client: AgentsClient, model_deployment: str, user_text: str) -> str:
    """
    Interpreta si el usuario dijo sí, no, o no está claro.
    Retorna: "yes", "no", o "unclear"
    """
    confirmation_agent = agents_client.create_agent(
        model=model_deployment,
        name="confirmation-agent",
        instructions=(
            "Eres un clasificador. Dado el último mensaje del usuario, "
            "responde SOLO en JSON:\n"
            '{ "confirmation": "yes" | "no" | "unclear" }\n'
            "No incluyas ningún texto adicional."
        ),
    )

    thread = agents_client.threads.create()
    agents_client.messages.create(
        thread_id=thread.id,
        role=MessageRole.USER,
        content=user_text,
    )

    run = agents_client.runs.create_and_process(
        thread_id=thread.id,
        agent_id=confirmation_agent.id,
    )

    messages = agents_client.messages.list(
        thread_id=thread.id,
        order=ListSortOrder.DESCENDING,
    )

    msg = next(
        (m for m in messages if m.role == MessageRole.AGENT and m.text_messages),
        None,
    )
    raw = msg.text_messages[-1].text.value if msg else "{}"

    agents_client.delete_agent(confirmation_agent.id)

    try:
        data = json.loads(raw)
        return data.get("confirmation", "unclear")
    except json.JSONDecodeError:
        return "unclear"


def generate_ux_message(agents_client: AgentsClient, model_deployment: str, state: Dict) -> str:
    """
    Genera un mensaje amigable para el usuario a partir de un estado estructurado
    """
    ux_agent = agents_client.create_agent(
        model=model_deployment,
        name="ux-agent",
        instructions=(
            "Eres un asistente de Service Desk. Recibirás un JSON con un campo 'mode', "
            "un objeto 'policy_decision' y, opcionalmente, 'extra_context'. "
            "Devuelve una respuesta breve, clara y empática en español para el usuario final. "
            "No muestres el JSON ni menciones que es un JSON."
        ),
    )

    thread = agents_client.threads.create()
    agents_client.messages.create(
        thread_id=thread.id,
        role=MessageRole.USER,
        content=json.dumps(state, ensure_ascii=False),
    )

    run = agents_client.runs.create_and_process(
        thread_id=thread.id,
        agent_id=ux_agent.id,
    )

    messages = agents_client.messages.list(
        thread_id=thread.id,
        order=ListSortOrder.DESCENDING,
    )

    msg = next(
        (m for m in messages if m.role == MessageRole.AGENT and m.text_messages),
        None,
    )
    text = msg.text_messages[-1].text.value if msg else ""

    agents_client.delete_agent(ux_agent.id)
    return text


def create_triage_agent(agents_client: AgentsClient, model_deployment: str, tools: list):
    """Crea el agente de Triage con las herramientas especificadas"""
    from prompts.prompts import TRIAGE_AGENT_INSTRUCTIONS

    print("🎯 Creando Triage Agent...")
    triage_agent = agents_client.create_agent(
        model=model_deployment,
        name="triage-support-agent",
        instructions=TRIAGE_AGENT_INSTRUCTIONS,
        tools=tools,
    )
    print(f"✅ Triage Agent creado: {triage_agent.id}")
    return triage_agent