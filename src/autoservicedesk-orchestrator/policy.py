"""
Evaluación de políticas con Policy Guard
"""
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import MessageRole, ListSortOrder
import json
from typing import Dict, Optional


def call_policy_guard(
        agents_client: AgentsClient,
        policy_agent_id: str,
        user_request: str,
        user_email: str,
        user_profile: Dict,
        thread_id: Optional[str] = None,
) -> Dict:
    """
    Llama al Policy Guard y retorna su decisión.

    Retorna:
        {
            "thread_id": str,
            "decision": {
                "risk_level": str,
                "reason": str,
                "policy_refs": list,
                "decision": "AUTO_APROBAR" | "REQUIERE_APROBACION" | "DENEGAR",
                "required_approver_role": str
            },
            "run_status": str
        }
    """
    if thread_id is None:
        thread = agents_client.threads.create()
        thread_id = thread.id
        print(f"✨ Nuevo thread (Policy Guard): {thread_id}")
    else:
        print(f"♻️ Reutilizando thread (Policy Guard): {thread_id}")

    payload = {
        "user_request": user_request,
        "user_email": user_email,
        "user_profile": user_profile,
    }

    agents_client.messages.create(
        thread_id=thread_id,
        role=MessageRole.USER,
        content=json.dumps(payload, ensure_ascii=False),
    )

    run = agents_client.runs.create_and_process(
        thread_id=thread_id,
        agent_id=policy_agent_id,
    )

    messages = agents_client.messages.list(
        thread_id=thread_id,
        order=ListSortOrder.DESCENDING,
    )

    policy_msg = next(
        (m for m in messages if m.role == MessageRole.AGENT and m.text_messages),
        None,
    )

    if not policy_msg:
        raise RuntimeError("Policy Guard no devolvió respuesta")

    raw_text = policy_msg.text_messages[-1].text.value
    try:
        decision = json.loads(raw_text)
    except json.JSONDecodeError:
        raise RuntimeError(f"Respuesta del Policy Guard no es JSON válido: {raw_text}")

    return {
        "thread_id": thread_id,
        "decision": decision,
        "run_status": run.status,
    }

