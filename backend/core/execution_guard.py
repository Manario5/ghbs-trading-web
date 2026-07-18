from typing import Dict, Any


class ExecutionNotAllowedError(RuntimeError):
    pass


def get_execution_guard_status() -> Dict[str, Any]:
    return {
        "broker_execution_enabled": False,
        "trade_write_enabled": False,
        "telegram_send_enabled": False,
        "scheduler_execution_enabled": False,
        "execution_enabled": False,
        "production_db_write_enabled": False,
    }


def verify_no_execution_side_effects() -> Dict[str, Any]:
    """
    Non-throwing guard for read-only/manual preview endpoints.

    It confirms that execution-related capabilities are disabled.
    This is safe to call before read-only analyze/scout preview.
    """
    status = get_execution_guard_status()
    unsafe = [
        key for key, value in status.items()
        if key.endswith("_enabled") and value is True
    ]

    if unsafe:
        raise ExecutionNotAllowedError(
            "Execution side effects are not allowed in this phase."
        )

    return status


def assert_no_execution_allowed():
    """
    Throwing guard for any actual execution/write/send path.

    Use this only before broker orders, real trade writes, Telegram sending,
    scheduler execution, or production DB writes.
    """
    raise ExecutionNotAllowedError("Execution is permanently disabled in this phase.")
