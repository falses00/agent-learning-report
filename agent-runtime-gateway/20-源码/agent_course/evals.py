from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .contracts import RunRequest
from .runtime import AgentRuntime


def run_eval(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    failures: list[dict[str, str]] = []

    for case in payload["cases"]:
        runtime = AgentRuntime()
        before = runtime.tool_execution_count("billing.refund")
        run = runtime.start(RunRequest.from_dict(case["request"]))

        if case.get("action") == "approve_twice":
            run = runtime.approve(run.run_id, "manager@example.com")
            run = runtime.approve(run.run_id, "manager@example.com")

        if run.status.value != case["expected_status"]:
            failures.append(
                {
                    "case_id": case["id"],
                    "reason": f"expected {case['expected_status']}, got {run.status.value}",
                }
            )
            continue

        if case.get("expected_refund_executions") is not None:
            executions = runtime.tool_execution_count("billing.refund") - before
            if executions != case["expected_refund_executions"]:
                failures.append(
                    {
                        "case_id": case["id"],
                        "reason": (
                            f"expected {case['expected_refund_executions']} refund executions, "
                            f"got {executions}"
                        ),
                    }
                )

    total = len(payload["cases"])
    return {"total": total, "passed": total - len(failures), "failed": len(failures), "failures": failures}
