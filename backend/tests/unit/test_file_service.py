from __future__ import annotations

import pytest
from app.core.exceptions import AppException
from app.services.file import validate_upload_content


def test_upload_validation_accepts_matching_pdf_signature() -> None:
    validate_upload_content("application/pdf", b"%PDF-1.7\ncontent")


def test_upload_validation_rejects_unsupported_type_and_mismatched_signature() -> None:
    with pytest.raises(AppException) as unsupported:
        validate_upload_content("text/plain", b"hello")
    assert unsupported.value.code == "FILE_TYPE_NOT_ALLOWED"

    with pytest.raises(AppException) as mismatched:
        validate_upload_content("image/png", b"not-a-png")
    assert mismatched.value.code == "FILE_CONTENT_INVALID"


def test_upload_validation_rejects_empty_content() -> None:
    with pytest.raises(AppException) as error:
        validate_upload_content("application/pdf", b"")
    assert error.value.code == "FILE_EMPTY"
