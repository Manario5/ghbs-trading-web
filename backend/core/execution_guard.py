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
    raise ExecutionNotAllowedError("Execution is permanently disabled in this phase.")
