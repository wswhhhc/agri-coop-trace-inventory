from __future__ import annotations

from scripts.test_gate import CRITICAL_COVERAGE_INCLUDE, build_gate_steps


def test_gate_runs_strict_tests_and_all_quality_checks() -> None:
    steps = build_gate_steps("uv")

    assert [step.name for step in steps] == [
        "pytest",
        "critical coverage",
        "mypy",
        "ruff",
    ]
    pytest_step = steps[0]
    assert "--cov-fail-under=70" in pytest_step.command
    assert pytest_step.environment == {
        "TEST_REQUIRE_POSTGRES": "1",
        "TEST_REQUIRE_REDIS": "1",
    }

    critical_step = steps[1]
    assert "--fail-under=80" in critical_step.command
    assert any(
        ",".join(CRITICAL_COVERAGE_INCLUDE) in argument
        for argument in critical_step.command
    )


def test_gate_checks_the_application_source_with_repository_tools() -> None:
    steps = build_gate_steps("uv")

    assert steps[0].command[:3] == ("uv", "run", "pytest")
    assert steps[2].command == ("uv", "run", "mypy", "backend/app")
    assert steps[3].command == ("uv", "run", "ruff", "check", ".")
