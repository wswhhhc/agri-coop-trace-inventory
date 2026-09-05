from __future__ import annotations

import ast
from pathlib import Path


def _method_calls(root: Path, method_name: str) -> list[str]:
    violations: list[str] = []
    for path in sorted(root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr == method_name:
                violations.append(f"{path}:{node.lineno}")
    return violations


def test_repositories_never_commit_transactions() -> None:
    repository_root = Path(__file__).resolve().parents[2] / "app" / "repositories"

    assert _method_calls(repository_root, "commit") == []


def test_api_dependencies_do_not_open_request_transactions() -> None:
    api_root = Path(__file__).resolve().parents[2] / "app" / "api"

    assert _method_calls(api_root, "get_transactional_session") == []
