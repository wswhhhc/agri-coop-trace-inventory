import re

import pytest
from app.utils.resource_codes import new_prefixed_code


@pytest.mark.parametrize("prefix", ["COOP", "WH", "CAT"])
def test_new_prefixed_code_uses_the_configured_resource_prefix(prefix: str) -> None:
    code = new_prefixed_code(prefix)

    assert re.fullmatch(rf"{prefix}-[A-Z0-9]{{6}}", code)


def test_new_prefixed_code_generates_distinct_codes_for_repeated_calls() -> None:
    codes = {new_prefixed_code("COOP") for _ in range(20)}

    assert len(codes) == 20
