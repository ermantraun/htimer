from types import SimpleNamespace
from typing import Any
from uuid import UUID, uuid4

import pytest

from htimer.application import common_exceptions, common_interfaces
from htimer.infrastructure.payment_gateway import gateway
from tests.integration import factories


@pytest.mark.asyncio
async def test_create_payment_success(
    infra_payment_gateway: common_interfaces.PaymentGateway,
    monkeypatch: pytest.MonkeyPatch,
):

    payment_id = str(uuid4())
    yookassa_payment = SimpleNamespace(
        confirmation=SimpleNamespace(confirmation_url="https://yookassa/confirm"),
        id=payment_id,
    )

    def _create_payment(_payload: dict[str, Any], idempotency_key: str) -> SimpleNamespace:
        return yookassa_payment

    monkeypatch.setattr(gateway.YooKassaPayment, "create", _create_payment)

    actor = factories.make_user_entity()
    project = factories.make_project_entity(creator=actor)
    payment = factories.make_payment_entity(subscription=factories.make_subscription_entity(project=project))

    result = await infra_payment_gateway.create_payment(actor, project, 100.0, payment)
    assert not isinstance(result, common_exceptions.PaymentFailedError)
    url, result_payment_id = result

    assert url == "https://yookassa/confirm"
    assert isinstance(result_payment_id, UUID)
    assert str(result_payment_id) == payment_id


@pytest.mark.asyncio
async def test_create_payment_confirmation_missing(
    infra_payment_gateway: common_interfaces.PaymentGateway,
    monkeypatch: pytest.MonkeyPatch,
):

    yookassa_payment = SimpleNamespace(confirmation=None, id=str(uuid4()))
    def _create_payment(_payload: dict[str, Any], idempotency_key: str) -> SimpleNamespace:
        return yookassa_payment

    monkeypatch.setattr(gateway.YooKassaPayment, "create", _create_payment)

    actor = factories.make_user_entity()
    project = factories.make_project_entity(creator=actor)
    payment = factories.make_payment_entity(subscription=factories.make_subscription_entity(project=project))

    with pytest.raises(common_exceptions.PaymentGatewayError):
        await infra_payment_gateway.create_payment(actor, project, 100.0, payment)


@pytest.mark.asyncio
async def test_verify_payment_complete_success(
    infra_payment_gateway: common_interfaces.PaymentGateway,
    monkeypatch: pytest.MonkeyPatch,
):

    def _find_one(_id: str) -> SimpleNamespace:
        return SimpleNamespace(status="succeeded")

    monkeypatch.setattr(gateway.YooKassaPayment, "find_one", _find_one)

    result = await infra_payment_gateway.verify_payment_complete(str(uuid4()))

    assert result is True


@pytest.mark.asyncio
async def test_verify_payment_complete_not_complete(
    infra_payment_gateway: common_interfaces.PaymentGateway,
    monkeypatch: pytest.MonkeyPatch,
):

    def _find_one(_id: str) -> SimpleNamespace:
        return SimpleNamespace(status="pending")

    monkeypatch.setattr(gateway.YooKassaPayment, "find_one", _find_one)

    result = await infra_payment_gateway.verify_payment_complete(str(uuid4()))

    assert result is False


@pytest.mark.asyncio
async def test_verify_payment_complete_gateway_error(
    infra_payment_gateway: common_interfaces.PaymentGateway,
    monkeypatch: pytest.MonkeyPatch,
):

    def _raise(_id: str):
        raise RuntimeError("boom")

    monkeypatch.setattr(gateway.YooKassaPayment, "find_one", _raise)

    with pytest.raises(common_exceptions.PaymentGatewayError):
        await infra_payment_gateway.verify_payment_complete(str(uuid4()))


@pytest.mark.asyncio
async def test_refund_payment_success(
    infra_payment_gateway: common_interfaces.PaymentGateway,
    monkeypatch: pytest.MonkeyPatch,
):

    def _create_refund(_payload: dict[str, Any], idempotency_key: str) -> SimpleNamespace:
        return SimpleNamespace(status="succeeded")

    monkeypatch.setattr(gateway.Refund, "create", _create_refund)

    owner = factories.make_user_entity()
    project = factories.make_project_entity(creator=owner)
    subscription = factories.make_subscription_entity(project=project)
    payment = factories.make_payment_entity(subscription=subscription)

    result = await infra_payment_gateway.refund_payment(payment, str(uuid4()))

    assert result is True


@pytest.mark.asyncio
async def test_refund_payment_failed(
    infra_payment_gateway: common_interfaces.PaymentGateway,
    monkeypatch: pytest.MonkeyPatch,
):

    def _create_refund(_payload: dict[str, Any], idempotency_key: str) -> SimpleNamespace:
        return SimpleNamespace(status="pending")

    monkeypatch.setattr(gateway.Refund, "create", _create_refund)

    owner = factories.make_user_entity()
    project = factories.make_project_entity(creator=owner)
    subscription = factories.make_subscription_entity(project=project)
    payment = factories.make_payment_entity(subscription=subscription)

    result = await infra_payment_gateway.refund_payment(payment, str(uuid4()))

    assert isinstance(result, common_exceptions.PaymentRefundFailedError)
