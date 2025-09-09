from typing import Dict


class TaskStatus:
    @staticmethod
    def get_meta(user_id: str, step: int, out_of: int, description: str, attempt: int) -> Dict[str, str]:
        return {
            "step": str(int(step)),
            "out_of": str(int(out_of)),
            "description": description,
            "user_id": user_id,
            "attempt": str(int(attempt))
        }