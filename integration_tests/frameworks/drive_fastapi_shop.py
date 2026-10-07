"""Drive the quote service in-process and print one JSON result per scenario.

Usage: python drive_fastapi_shop.py <app_dir>

Run once against the original sources and once against the obfuscated
output; the two printed documents must be identical. The last scenario
raises inside the app on purpose, and its traceback is printed to stderr so
the test can unmap it.
"""

import json
import sys
import traceback

sys.path.insert(0, sys.argv[1])

from fastapi.testclient import TestClient  # noqa: E402

import app as app_module  # noqa: E402

client = TestClient(app_module.app)
results = []


def record(name, response):
    results.append({"scenario": name, "status": response.status_code, "body": response.json()})


record("health", client.get("/health"))
record(
    "quote_partner_volume",
    client.post(
        "/quote",
        json={
            "customer_tier": "partner",
            "lines": [
                {"sku": "ABC-1", "quantity": 10, "unit_price": 99.5},
                {"sku": "XYZ-9", "quantity": 1, "unit_price": 12.25},
            ],
        },
    ),
)
record(
    "quote_default_tier",
    client.post("/quote", json={"lines": [{"sku": "ABC-1", "quantity": 2, "unit_price": 3.0}]}),
)
record(
    "reject_unknown_tier",
    client.post(
        "/quote",
        json={"customer_tier": "gold", "lines": [{"sku": "ABC-1", "quantity": 1, "unit_price": 1}]},
    ),
)
record(
    "reject_bad_line",
    client.post("/quote", json={"lines": [{"sku": "A", "quantity": 0, "unit_price": -1}]}),
)
record("margin", client.get("/margin", params={"revenue": 200, "cost": 150}))
record("margin_missing_param", client.get("/margin", params={"revenue": 200}))

# Pydantic error payloads carry the input and a docs URL that can change
# between pydantic releases; keep only what the API contract promises.
for item in results:
    if item["status"] == 422:
        item["body"] = sorted((tuple(err["loc"]), err["type"]) for err in item["body"]["detail"])

try:
    client.get("/margin", params={"revenue": 0, "cost": 1})
except ZeroDivisionError:
    traceback.print_exc()

print(json.dumps(results, indent=2, sort_keys=True))
