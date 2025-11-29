"""
Gestión de contexto de conversaciones
"""
from typing import Dict

# Contexto global en memoria
_conversation_context: Dict[str, Dict] = {}


def get_context(thread_id: str) -> Dict:
    """Obtiene el contexto de una conversación"""
    return _conversation_context.get(thread_id, {
        "awaiting_work_item_confirmation": False,
        "last_denied_request": None,
        "last_policy_decision": None,
    })


def update_context(thread_id: str, new_context: Dict) -> None:
    """Actualiza el contexto de una conversación"""
    _conversation_context[thread_id] = new_context
    print(f"[CTX] Contexto actualizado para thread {thread_id}")


def clear_confirmation_flag(thread_id: str) -> None:
    """Limpia el flag de espera de confirmación"""
    context = get_context(thread_id)
    context["awaiting_work_item_confirmation"] = False
    update_context(thread_id, context)


def set_waiting_confirmation(thread_id: str, request: str, policy_decision: Dict) -> None:
    """Marca que se está esperando confirmación"""
    context = get_context(thread_id)
    context["awaiting_work_item_confirmation"] = True
    context["last_denied_request"] = request
    context["last_policy_decision"] = policy_decision
    update_context(thread_id, context)