# Simple guardrails for user input
# Place this in app_agents/guardrails.py
import re
from typing import Tuple

BLOCKED_KEYWORDS = [
    "kill", "attack", "hack", "exploit", "bomb", "terror", "suicide", "drugs", "violence", "porn", "nude", "racist", "hate", "murder"
]

BLOCKED_PATTERNS = [
    re.compile(r"\b(?:" + "|".join(BLOCKED_KEYWORDS) + r")\b", re.IGNORECASE)
]

BLOCKED_PROMPT = "⚠️ Your message was blocked by safety guardrails. Please rephrase."


def check_guardrails(user_message: str) -> Tuple[bool, str]:
    """
    Returns (is_blocked, message). If blocked, message is the reason.
    """
    for pattern in BLOCKED_PATTERNS:
        if pattern.search(user_message):
            return True, BLOCKED_PROMPT
    return False, ""
