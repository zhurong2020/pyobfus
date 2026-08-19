# Demo module whose identifiers we want to protect BEFORE it is compiled to a
# C extension. Names are intentionally obvious so the README's verification
# step has something to grep for.

API_SECRET = "super-secret-value"
BUSINESS_RULE = "core logic"


def proprietary_transform(x: int) -> int:
    return x * 42 + len(BUSINESS_RULE)


class ConfidentialEngine:
    def run(self, payload: str) -> str:
        return f"{API_SECRET}:{payload}"
