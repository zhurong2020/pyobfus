"""Fixture with a deliberate obfuscation risk, used by the integration
test suite (test/suite/integration.test.ts) to assert against real
`pyobfus --check --json` output, not a mocked stand-in."""


def compute(expression):
    return eval(expression)  # dynamic_exec, severity=high
