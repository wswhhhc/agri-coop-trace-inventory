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


def test_catalog_and_batch_repositories_require_scope_conditions() -> None:
    repository_root = Path(__file__).resolve().parents[2] / "app" / "repositories"
    for filename in ("product_category.py", "product.py", "batch.py"):
        tree = ast.parse(
            (repository_root / filename).read_text(encoding="utf-8"),
            filename=str(repository_root / filename),
        )
        methods = {
            node.name: node
            for node in ast.walk(tree)
            if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef))
        }
        assert {"get_scoped", "list_scoped", "_scope_conditions"} <= methods.keys()
        for method_name in ("get_scoped", "list_scoped"):
            assert any(
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "_scope_conditions"
                for node in ast.walk(methods[method_name])
            ), f"{filename}:{method_name} must apply data scope"
