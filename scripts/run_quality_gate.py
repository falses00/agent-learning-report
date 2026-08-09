from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "agent-runtime-gateway" / "20-源码"


@dataclass(frozen=True)
class Check:
    name: str
    command: tuple[str, ...]
    cwd: Path
    report_name: str
    generated_files: tuple[str, ...] = field(default_factory=tuple)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _commit_sha() -> str:
    if value := os.environ.get("GITHUB_SHA"):
        return value
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def _working_tree_dirty() -> bool | None:
    result = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return bool(result.stdout.strip()) if result.returncode == 0 else None


def _runtime_version(command: list[str]) -> str:
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
    except OSError:
        return "unavailable"
    return result.stdout.strip() if result.returncode == 0 else "unavailable"


def _display_command(command: tuple[str, ...]) -> str:
    normalized = ("python", *command[1:]) if command[0] == sys.executable else command
    return shlex.join(normalized)


def _display_path(path: Path, *, fallback_base: Path | None = None) -> str:
    try:
        return path.relative_to(ROOT).as_posix() or "."
    except ValueError:
        if fallback_base is not None:
            try:
                return path.relative_to(fallback_base).as_posix() or "."
            except ValueError:
                pass
        return path.name or "."


def _run(check: Check, output_dir: Path) -> dict[str, object]:
    report_path = output_dir / check.report_name
    expected_paths = [report_path]
    expected_paths.extend(output_dir / name for name in check.generated_files)
    for path in expected_paths:
        path.unlink(missing_ok=True)

    started = time.perf_counter()
    try:
        result = subprocess.run(
            check.command,
            cwd=check.cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError as exc:
        result = subprocess.CompletedProcess(
            check.command,
            127,
            stdout="",
            stderr=f"{type(exc).__name__}: {exc}\n",
        )
    duration_ms = round((time.perf_counter() - started) * 1000)
    extra_artifacts: list[Path] = []
    if report_path.suffix == ".json" and result.stdout.strip():
        try:
            payload = json.loads(result.stdout)
            report_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        except json.JSONDecodeError:
            report_path.write_text(result.stdout, encoding="utf-8")
        if result.stderr:
            stderr_path = report_path.with_suffix(report_path.suffix + ".stderr.log")
            stderr_path.write_text(result.stderr, encoding="utf-8")
            extra_artifacts.append(stderr_path)
    else:
        combined = result.stdout
        if result.stderr:
            combined += ("\n" if combined else "") + "[stderr]\n" + result.stderr
        report_path.write_text(combined, encoding="utf-8")

    print(f"[{check.name}] exit={result.returncode} duration_ms={duration_ms}")
    if result.stdout:
        print(result.stdout.rstrip())
    if result.stderr:
        print(result.stderr.rstrip(), file=sys.stderr)

    artifact_paths = [report_path]
    artifact_paths.extend(output_dir / name for name in check.generated_files)
    artifact_paths.extend(extra_artifacts)
    artifacts = [
        {
            "path": _display_path(path, fallback_base=output_dir),
            "sha256": _sha256(path),
            "bytes": path.stat().st_size,
        }
        for path in artifact_paths
        if path.exists()
    ]
    return {
        "name": check.name,
        "command": _display_command(check.command),
        "cwd": _display_path(check.cwd),
        "status": "passed" if result.returncode == 0 else "failed",
        "exit_code": result.returncode,
        "duration_ms": duration_ms,
        "artifacts": artifacts,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the same content, test, and eval gates locally and in CI."
    )
    parser.add_argument("--output-dir", default="quality-reports")
    args = parser.parse_args()
    output_dir = (ROOT / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    pytest_xml = output_dir / "pytest.xml"
    try:
        pytest_xml_argument = os.path.relpath(pytest_xml, SOURCE_DIR)
    except ValueError:
        pytest_xml_argument = str(pytest_xml)
    checks = (
        Check("chapters", ("node", "data/build_chapters.mjs", "--check"), ROOT, "chapters.log"),
        Check(
            "baseline-metrics",
            ("node", "data/build_baseline_metrics.mjs", "--check"),
            ROOT,
            "baseline-metrics.log",
        ),
        Check("course-gate", ("node", "data/check_course_gate.mjs"), ROOT, "course-gate.log"),
        Check(
            "learning-content",
            ("node", "data/check_learning_content.mjs"),
            ROOT,
            "learning-content.log",
        ),
        Check(
            "memory-content",
            ("node", "data/check_memory_content.mjs"),
            ROOT,
            "memory-content.log",
        ),
        Check(
            "rag-content",
            ("node", "data/check_rag_content.mjs"),
            ROOT,
            "rag-content.log",
        ),
        Check(
            "eval-content",
            ("node", "data/check_eval_content.mjs"),
            ROOT,
            "eval-content.log",
        ),
        Check(
            "observability-content",
            ("node", "data/check_observability_content.mjs"),
            ROOT,
            "observability-content.log",
        ),
        Check(
            "security-content",
            ("node", "data/check_security_content.mjs"),
            ROOT,
            "security-content.log",
        ),
        Check(
            "vibe-coding-content",
            ("node", "data/check_vibe_coding_content.mjs"),
            ROOT,
            "vibe-coding-content.log",
        ),
        Check(
            "pytest",
            (
                sys.executable,
                "-m",
                "pytest",
                "../21-测试",
                "-q",
                f"--junitxml={pytest_xml_argument}",
            ),
            SOURCE_DIR,
            "pytest.log",
            ("pytest.xml",),
        ),
        Check(
            "engineering-eval",
            (
                sys.executable,
                "-m",
                "agent_course.cli",
                "eval",
                "../22-评测集/engineering-baseline.json",
            ),
            SOURCE_DIR,
            "engineering-eval.json",
        ),
        Check(
            "s3-rag-eval",
            (
                sys.executable,
                "-m",
                "agent_course.cli",
                "eval",
                "../22-评测集/s3-rag-baseline.json",
            ),
            SOURCE_DIR,
            "s3-rag-eval.json",
        ),
        Check(
            "s3-rag-diagnostic-eval",
            (
                sys.executable,
                "-m",
                "agent_course.cli",
                "rag-diagnostic-eval",
                "../22-评测集/rag-diagnostic-baseline.json",
            ),
            SOURCE_DIR,
            "s3-rag-diagnostic-eval.json",
        ),
        Check(
            "s4-durable-eval",
            (
                sys.executable,
                "-m",
                "agent_course.cli",
                "eval",
                "../22-评测集/s4-durable-baseline.json",
            ),
            SOURCE_DIR,
            "s4-durable-eval.json",
        ),
        Check(
            "s5-memory-eval",
            (
                sys.executable,
                "-m",
                "agent_course.cli",
                "memory-eval",
                "../22-评测集/memory-engineering-baseline.jsonl",
            ),
            SOURCE_DIR,
            "s5-memory-eval.json",
        ),
        Check(
            "s6-release-gate",
            (
                sys.executable,
                "-m",
                "agent_course.cli",
                "release-gate",
                "../22-评测集/s6-release-manifest.json",
            ),
            SOURCE_DIR,
            "s6-release-gate.json",
        ),
        Check(
            "s6-gate-adversarial",
            (
                sys.executable,
                "-m",
                "agent_course.cli",
                "release-gate-eval",
                "../22-评测集/s6-release-gate-adversarial.json",
            ),
            SOURCE_DIR,
            "s6-gate-adversarial.json",
        ),
        Check(
            "s7-observability",
            (
                sys.executable,
                "-m",
                "agent_course.cli",
                "observability",
                "../22-评测集/s7-observability-manifest.json",
            ),
            SOURCE_DIR,
            "s7-observability.json",
        ),
        Check(
            "s7-observability-adversarial",
            (
                sys.executable,
                "-m",
                "agent_course.cli",
                "observability-eval",
                "../22-评测集/s7-observability-adversarial.json",
            ),
            SOURCE_DIR,
            "s7-observability-adversarial.json",
        ),
        Check(
            "s8-security-adversarial",
            (
                sys.executable,
                "-m",
                "agent_course.cli",
                "security-eval",
                "../22-评测集/s8-security-adversarial.json",
            ),
            SOURCE_DIR,
            "s8-security-adversarial.json",
        ),
    )

    results = [_run(check, output_dir) for check in checks]
    release_passed = all(item["status"] == "passed" for item in results)
    manifest = {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "commit_sha": _commit_sha(),
        "source_dirty": _working_tree_dirty(),
        "release_passed": release_passed,
        "environment": {
            "python": platform.python_version(),
            "node": _runtime_version(["node", "--version"]),
            "platform": platform.platform(),
            "ci": bool(os.environ.get("CI")),
            "github_run_id": os.environ.get("GITHUB_RUN_ID"),
            "github_run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
        },
        "summary": {
            "total": len(results),
            "passed": sum(item["status"] == "passed" for item in results),
            "failed": sum(item["status"] == "failed" for item in results),
        },
        "checks": results,
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"[quality-gate] release_passed={release_passed} "
        f"checks={manifest['summary']['passed']}/{manifest['summary']['total']} "
        f"manifest={_display_path(manifest_path, fallback_base=output_dir)}"
    )
    return 0 if release_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
