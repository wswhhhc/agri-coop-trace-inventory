from __future__ import annotations

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CRITICAL_COVERAGE_INCLUDE = (
    "backend/app/models/*",
    "backend/app/core/auth/*",
    "backend/app/core/exceptions.py",
    "backend/app/infrastructure/*",
)


@dataclass(frozen=True)
class GateStep:
    name: str
    command: tuple[str, ...]
    environment: dict[str, str]


def build_gate_steps(uv_executable: str) -> tuple[GateStep, ...]:
    """返回公共测试门禁的固定检查步骤。"""
    strict_environment = {
        "TEST_REQUIRE_POSTGRES": "1",
        "TEST_REQUIRE_REDIS": "1",
    }
    return (
        GateStep(
            "pytest",
            (
                uv_executable,
                "run",
                "pytest",
                "-q",
                "--cov=backend/app",
                "--cov-report=term-missing",
                "--cov-report=json:coverage.json",
                "--cov-fail-under=70",
            ),
            strict_environment,
        ),
        GateStep(
            "critical coverage",
            (
                uv_executable,
                "run",
                "coverage",
                "report",
                f"--include={','.join(CRITICAL_COVERAGE_INCLUDE)}",
                "--fail-under=80",
            ),
            {},
        ),
        GateStep(
            "mypy",
            (uv_executable, "run", "mypy", "backend/app"),
            {},
        ),
        GateStep(
            "ruff",
            (uv_executable, "run", "ruff", "check", "."),
            {},
        ),
    )


def _run_step(step: GateStep) -> int:
    environment = os.environ.copy()
    environment.update(step.environment)
    print(f"\n[门禁] {step.name}: {' '.join(step.command)}", flush=True)
    try:
        result = subprocess.run(
            step.command,
            cwd=PROJECT_ROOT,
            env=environment,
            check=False,
        )
    except OSError as error:
        print(f"[门禁] {step.name} 无法执行：{error}", file=sys.stderr)
        return 1
    return result.returncode


def main() -> int:
    uv_executable = shutil.which("uv")
    if uv_executable is None:
        print("[门禁] 未找到 uv，请先安装 uv。", file=sys.stderr)
        return 1

    failures: list[str] = []
    for step in build_gate_steps(uv_executable):
        if _run_step(step) != 0:
            failures.append(step.name)

    if failures:
        print(f"\n[门禁] 失败步骤：{', '.join(failures)}", file=sys.stderr)
        return 1
    print("\n[门禁] 全部通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
