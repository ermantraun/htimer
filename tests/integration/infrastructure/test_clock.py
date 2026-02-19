from application import common_interfaces
from application.common_exceptions import InvalidDate
from datetime import datetime


async def test_now_date_returns_datetime(
    infra_clock: common_interfaces.Clock,
):
    value = await infra_clock.now_date()

    assert isinstance(value, datetime)
    assert value.tzinfo is not None


def test_verify_date_valid(
    infra_clock: common_interfaces.Clock,
):
    result = infra_clock.verify_date("2026-02-17")

    assert result == "2026-02-17"


def test_verify_date_invalid(
    infra_clock: common_interfaces.Clock,
):
    result = infra_clock.verify_date("17-02-2026")

    assert isinstance(result, InvalidDate)
