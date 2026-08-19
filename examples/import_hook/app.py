# Demo module whose identifiers we want to protect BEFORE it is loaded
# through a custom import hook. The names below are intentionally obvious so
# the "verify names are mangled" step in the README has something to grep for.

API_TOKEN = "super-secret-value"
PROPRIETARY_LOGIC = "core business rule"


def top_secret_algorithm(x: int) -> int:
    return x * 42 + len(PROPRIETARY_LOGIC)


class ConfidentialService:
    def handle(self, payload: str) -> str:
        return f"{API_TOKEN}:{payload}"
