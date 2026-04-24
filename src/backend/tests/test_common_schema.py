from pydantic import ValidationError
import pytest

from app.schemas.common import ApiResponse


def test_api_response_requires_code_message_and_data() -> None:
    payload = ApiResponse[dict[str, str]](
        code="OK",
        message="done",
        data={"hello": "world"},
    )

    assert payload.code == "OK"
    assert payload.message == "done"
    assert payload.data == {"hello": "world"}


def test_api_response_allows_empty_data_for_future_error_cases() -> None:
    payload = ApiResponse[dict[str, str]](
        code="OK",
        message="done",
    )

    assert payload.data is None


def test_api_response_rejects_missing_message() -> None:
    with pytest.raises(ValidationError):
        ApiResponse[dict[str, str]](
            code="OK",
            data={},
        )
