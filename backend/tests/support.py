from __future__ import annotations

import os
from typing import NoReturn

import pytest


def skip_or_fail(service: str, reason: str) -> NoReturn:
    """普通测试允许跳过，严格门禁模式下将基础设施缺失升级为失败。"""
    if os.getenv(f"TEST_REQUIRE_{service.upper()}") == "1":
        pytest.fail(reason)
    pytest.skip(reason)
