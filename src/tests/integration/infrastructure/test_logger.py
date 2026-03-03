import pytest

from application import common_interfaces


async def test_logger_info_prints_message(
    infra_logger: common_interfaces.Logger,
    capsys: pytest.CaptureFixture[str],
):
    await infra_logger.info("CreateUser", "created")

    output = capsys.readouterr().out
    assert "[INFO]" in output
    assert "CreateUser" in output
    assert "created" in output
