from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "run_quality_gate.py"
SPEC = importlib.util.spec_from_file_location("run_quality_gate", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
quality_gate = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = quality_gate
SPEC.loader.exec_module(quality_gate)


def test_failed_check_is_reported_with_replayable_evidence(tmp_path) -> None:
    check = quality_gate.Check(
        name="intentional-failure",
        command=(sys.executable, "-c", "import sys; print('failure evidence'); sys.exit(7)"),
        cwd=tmp_path,
        report_name="intentional-failure.log",
    )

    result = quality_gate._run(check, tmp_path)

    assert result["status"] == "failed"
    assert result["exit_code"] == 7
    assert result["artifacts"][0]["sha256"]
    assert (tmp_path / "intentional-failure.log").read_text(encoding="utf-8") == (
        "failure evidence\n"
    )


def test_missing_executable_fails_without_reusing_stale_artifact(tmp_path) -> None:
    stale = tmp_path / "generated.xml"
    stale.write_text("stale", encoding="utf-8")
    check = quality_gate.Check(
        name="missing-runtime",
        command=("definitely-not-an-installed-command",),
        cwd=tmp_path,
        report_name="missing-runtime.log",
        generated_files=("generated.xml",),
    )

    result = quality_gate._run(check, tmp_path)

    assert result["status"] == "failed"
    assert result["exit_code"] == 127
    assert not stale.exists()
    assert [artifact["path"] for artifact in result["artifacts"]] == [
        "missing-runtime.log"
    ]
    assert "FileNotFoundError" in (tmp_path / "missing-runtime.log").read_text(
        encoding="utf-8"
    )
