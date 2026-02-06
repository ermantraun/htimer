from uuid import uuid4
from typing import Any
from datetime import timedelta
import common_exceptions,common_interfaces
from domain import entities
import dto,  interfaces, exceptions


class CreateSubscriptionInteractor:
    def __init__(
        self,
        subscription_repository: common_interfaces.SubscriptionRepository,
        user_repository: common_interfaces.UserRepository,
        project_repository: common_interfaces.ProjectRepository,
        context: common_interfaces.UserContext,
        clock: common_interfaces.Clock,
        authorization_policy: interfaces.SubscriptionAuthorizationPolicy,
    ):
        self.subscription_repository = subscription_repository
        self.user_repository = user_repository
        self.context = context
        self.clock = clock
        self.authorization_policy = authorization_policy
        self.project_repository = project_repository
        
    async def execute(self, data: dto.CreateSubscriptionInDTO) -> dto.CreateSubscriptionOutDTO | common_exceptions.SubscriptionAlreadyExistsError | common_exceptions.ProjectNotFoundError | common_exceptions.InvalidToken | common_exceptions.UserNotFoundError | exceptions.SubscriptionAuthorizationError | exceptions.CantCreateSubscription | common_exceptions.UserRepositoryError | common_exceptions.ProjectRepositoryError | common_exceptions.SubscriptionRepositoryError:
        actor_uuid = self.context.get_current_user_uuid()
        if isinstance(actor_uuid, common_exceptions.InvalidToken):
            raise actor_uuid

        actor = await self.user_repository.get_by_uuid(actor_uuid)
        if isinstance(actor, (common_exceptions.UserNotFoundError, common_exceptions.UserRepositoryError)):
            raise actor

        project = await self.project_repository.get_by_uuid(data.project_uuid)
        if isinstance(project, (common_exceptions.ProjectNotFoundError, common_exceptions.ProjectRepositoryError)):
            raise project


        authorization_error = self.authorization_policy.decide_create_subscription(
            actor=actor,
            project=project,

        )
        if authorization_error is not None:
            raise authorization_error

        new_subscription = entities.Subscription(
            uuid=uuid4(),
            project=project,
            created_at=self.clock.now_date(),
        )

        ensure_err = new_subscription.ensure_create()
        if ensure_err:
            raise exceptions.CantCreateSubscription(ensure_err)

        created_subscription = await self.subscription_repository.create(new_subscription)
        if isinstance(created_subscription, (common_exceptions.SubscriptionAlreadyExistsError, common_exceptions.ProjectNotFoundError, common_exceptions.SubscriptionRepositoryError)):
            raise created_subscription

        return dto.CreateSubscriptionOutDTO(created_subscription)

class UpdateSubscriptionInteractor:
    def __init__(
        self,
        subscription_repository: common_interfaces.SubscriptionRepository,
        user_repository: common_interfaces.UserRepository,
        project_repository: common_interfaces.ProjectRepository,
        context: common_interfaces.UserContext,
        clock: common_interfaces.Clock,
        authorization_policy: interfaces.SubscriptionAuthorizationPolicy,
    ):
        self.subscription_repository = subscription_repository
        self.user_repository = user_repository
        self.project_repository = project_repository
        self.context = context
        self.clock = clock
        self.authorization_policy = authorization_policy

    async def execute(self, data: dto.UpdateSubscriptionInDTO) -> None | common_exceptions.SubscriptionNotFoundError | common_exceptions.ProjectNotFoundError | common_exceptions.InvalidToken | common_exceptions.UserNotFoundError | exceptions.SubscriptionAuthorizationError | exceptions.CantUpdateSubscription | common_exceptions.UserRepositoryError | common_exceptions.ProjectRepositoryError | common_exceptions.SubscriptionRepositoryError:

        actor_uuid = self.context.get_current_user_uuid()
        if isinstance(actor_uuid, common_exceptions.InvalidToken):
            raise actor_uuid

        actor = await self.user_repository.get_by_uuid(actor_uuid)
        if isinstance(actor, (common_exceptions.UserNotFoundError, common_exceptions.UserRepositoryError)):
            raise actor

        project = await self.project_repository.get_by_uuid(data.project_uuid)
        if isinstance(project, (common_exceptions.ProjectNotFoundError, common_exceptions.ProjectRepositoryError)):
            raise project

        auth_err = self.authorization_policy.decide_update_subscription(actor=actor, project=project)
        if auth_err is not None:
            raise auth_err

        subscription = await self.subscription_repository.get_active_subscription(data.project_uuid)
        if isinstance(subscription, (common_exceptions.SubscriptionNotFoundError, common_exceptions.ProjectNotFoundError, common_exceptions.SubscriptionRepositoryError)):
            raise subscription

        ensure_err = subscription.ensure_update(entities.SubscriptionStatus(data.status))
        
        if ensure_err:
            raise exceptions.CantUpdateSubscription(ensure_err)

        update_result = await self.subscription_repository.update(
            subscription_uuid=subscription.uuid,
            data={'status': entities.SubscriptionStatus.CANCELLED,
                  'auto_renew': data.auto_renew,
                  'end_date': None}
        )

        if isinstance(update_result, (common_exceptions.SubscriptionNotFoundError, common_exceptions.SubscriptionRepositoryError)):
            raise update_result

        return None


class ExtendSubscriptionInteractor:
    def __init__(
        self,
        subscription_repository: common_interfaces.SubscriptionRepository,
        project_repository: common_interfaces.ProjectRepository,
        payment_repository: common_interfaces.PaymentRepository,
        payment_gateway: common_interfaces.PaymentGateway,
        clock: common_interfaces.Clock,
    ):
        self.subscription_repository = subscription_repository
        self.project_repository = project_repository
        self.clock = clock
        self.payment_repository = payment_repository
        self.payment_gateway = payment_gateway
    async def execute(self, data: dto.ExtendSubscriptionInDTO) -> None | common_exceptions.SubscriptionNotFoundError | common_exceptions.ProjectNotFoundError | exceptions.CantExtendSubscription | common_exceptions.PaymentNotFoundError | common_exceptions.PaymentNotComplete | common_exceptions.PaymentNotExistsError | common_exceptions.ProjectRepositoryError | common_exceptions.SubscriptionRepositoryError | common_exceptions.PaymentRepositoryError:

        project = await self.project_repository.get_by_uuid(data.project_uuid)
        if isinstance(project, (common_exceptions.ProjectNotFoundError, common_exceptions.ProjectRepositoryError)):
            raise project

        subscription = await self.subscription_repository.get_active_subscription(data.project_uuid)
        if isinstance(subscription, (common_exceptions.SubscriptionNotFoundError, common_exceptions.ProjectNotFoundError, common_exceptions.SubscriptionRepositoryError)):
            raise subscription

        payment = await self.payment_repository.get_by_uuid(data.payment_uuid)
        
        if isinstance(payment, (common_exceptions.PaymentNotFoundError, common_exceptions.PaymentRepositoryError)):
            raise payment
        
        verify = await self.payment_gateway.verify_payment(payment.uuid)
        
        if isinstance(verify, common_exceptions.PaymentNotComplete) or isinstance(verify, common_exceptions.PaymentNotExistsError):
            raise verify
        
        ensure_res = subscription.ensure_extend()

        if ensure_res:
            raise exceptions.CantExtendSubscription(ensure_res)
        
        update_data: dict[str, Any] = {'status': entities.SubscriptionStatus.ACTIVE}


        if payment.payment_date is not None:
            update_data['end_date'] = self.clock.now_date() + timedelta(30)
        else:
            raise exceptions.CantExtendSubscription("Платёж не завершён, невозможно продлить подписку.")
            

        update_res = await self.subscription_repository.update(
            subscription_uuid=subscription.uuid,
            data=update_data
        )

        if isinstance(update_res, (common_exceptions.SubscriptionNotFoundError, common_exceptions.SubscriptionRepositoryError)):
            raise update_res

        return None
    
class ActivateSubscriptionInteractor:
    def __init__(
        self,
        subscription_repository: common_interfaces.SubscriptionRepository,
        project_repository: common_interfaces.ProjectRepository,
        clock: common_interfaces.Clock,
    ):
        self.subscription_repository = subscription_repository
        self.project_repository = project_repository
        self.clock = clock
    async def execute(self, data: dto.ActivateSubscriptionInDTO) -> None | common_exceptions.SubscriptionNotFoundError | common_exceptions.ProjectNotFoundError | exceptions.CantActivateSubscription | common_exceptions.PaymentNotFoundError | common_exceptions.PaymentNotComplete | common_exceptions.PaymentNotExistsError | common_exceptions.ProjectRepositoryError | common_exceptions.SubscriptionRepositoryError:

        project = await self.project_repository.get_by_uuid(data.project_uuid)
        if isinstance(project, (common_exceptions.ProjectNotFoundError, common_exceptions.ProjectRepositoryError)):
            raise project

        subscription = await self.subscription_repository.get_by_project_uuid(data.project_uuid)
        if isinstance(subscription, (common_exceptions.SubscriptionNotFoundError, common_exceptions.ProjectNotFoundError, common_exceptions.SubscriptionRepositoryError)):
            raise subscription

        ensure_res = subscription.ensure_activate()

        if ensure_res:
            raise exceptions.CantActivateSubscription(ensure_res)
        
        update_res = await self.subscription_repository.update(
            subscription_uuid=subscription.uuid,
            data={'status': entities.SubscriptionStatus.ACTIVE,
                  'start_date': self.clock.now_date(),
                  'end_date': self.clock.now_date() + timedelta(30)}
        )

        if isinstance(update_res, (common_exceptions.SubscriptionNotFoundError, common_exceptions.SubscriptionRepositoryError)):
            raise update_res

        return None
    
class CreatePaymentInteractor:
    def __init__(
        self,
        subscription_repository: common_interfaces.SubscriptionRepository,
        payment_repository: common_interfaces.PaymentRepository,
        user_repository: common_interfaces.UserRepository,
        project_repository: common_interfaces.ProjectRepository,
        context: common_interfaces.UserContext,
        clock: common_interfaces.Clock,
        authorization_policy: interfaces.SubscriptionAuthorizationPolicy,
        payment_gateway: common_interfaces.PaymentGateway,
    ):
        self.subscription_repository = subscription_repository
        self.user_repository = user_repository
        self.context = context
        self.clock = clock
        self.authorization_policy = authorization_policy
        self.project_repository = project_repository
        self.payment_repository = payment_repository
        self.payment_gateway = payment_gateway
        
    async def execute(self, data: dto.CreatePaymentInDTO) -> dto.CreatePaymentOutDTO | common_exceptions.SubscriptionNotFoundError | common_exceptions.ProjectNotFoundError | common_exceptions.InvalidToken | common_exceptions.UserNotFoundError | exceptions.SubscriptionAuthorizationError | exceptions.CantCreateSubscription | common_exceptions.PaymentFailedError | exceptions.CantCreatePayment | common_exceptions.UserRepositoryError | common_exceptions.ProjectRepositoryError | common_exceptions.SubscriptionRepositoryError | common_exceptions.PaymentRepositoryError:
        actor_uuid = self.context.get_current_user_uuid()
        if isinstance(actor_uuid, common_exceptions.InvalidToken):
            raise actor_uuid

        actor = await self.user_repository.get_by_uuid(actor_uuid)
        if isinstance(actor, (common_exceptions.UserNotFoundError, common_exceptions.UserRepositoryError)):
            raise actor

        project = await self.project_repository.get_by_uuid(data.project_uuid)
        if isinstance(project, (common_exceptions.ProjectNotFoundError, common_exceptions.ProjectRepositoryError)):
            raise project


        authorization_error = self.authorization_policy.decide_create_payment(
            actor=actor,
            project=project,

        )
        if authorization_error is not None:
            raise authorization_error

        subscription = await self.subscription_repository.get_by_project_uuid(data.project_uuid)
        if isinstance(subscription, (common_exceptions.SubscriptionNotFoundError, common_exceptions.ProjectNotFoundError, common_exceptions.SubscriptionRepositoryError)):
            raise subscription

        payment = entities.Payment(
            uuid=uuid4(),
            subscription=subscription,
            amount=entities.value_objects.MoneyAmount(amount=data.amount, currency=entities.value_objects.CurrencyEnum(data.currency)),
            created_at=self.clock.now_date(),
        )

        ensure_err = payment.ensure_create()
        if ensure_err:
            raise exceptions.CantCreatePayment(ensure_err)

        payment =  await self.payment_repository.create(payment)
        
        if isinstance(payment, (common_exceptions.SubscriptionNotFoundError, common_exceptions.PaymentRepositoryError)):
            raise payment
        
        payment_link = await self.payment_gateway.get_process_payment_link(
            amount=data.amount,
            payment=payment
        )
        if isinstance(payment_link, common_exceptions.PaymentFailedError):
            raise payment_link

        return dto.CreatePaymentOutDTO(payment_link)
    
    
class CompletePaymentInteractor:
    def __init__(
        self,
        payment_repository: common_interfaces.PaymentRepository,
        user_repository: common_interfaces.UserRepository,
        project_repository: common_interfaces.ProjectRepository,
        clock: common_interfaces.Clock,
        payment_gateway: common_interfaces.PaymentGateway,
    ):
        self.user_repository = user_repository
        self.clock = clock
        self.project_repository = project_repository
        self.payment_repository = payment_repository
        self.payment_gateway = payment_gateway

    async def execute(self, data: dto.CompletePaymentInDTO) -> None | common_exceptions.SubscriptionNotFoundError | common_exceptions.ProjectNotFoundError | common_exceptions.PaymentNotFoundError | exceptions.CantCompletePayment | common_exceptions.PaymentNotComplete | common_exceptions.PaymentNotExistsError | common_exceptions.PaymentRepositoryError:
        
        payment = await self.payment_repository.get_by_uuid(data.payment_uuid, lock_record=True)
        if isinstance(payment, (common_exceptions.PaymentNotFoundError, common_exceptions.PaymentRepositoryError)):
            raise payment

        is_verified = await self.payment_gateway.verify_payment(data.payment_uuid)
        if isinstance(is_verified, common_exceptions.PaymentNotComplete) or isinstance(is_verified, common_exceptions.PaymentNotExistsError):
            raise is_verified

        if not is_verified:
            raise exceptions.CantCompletePayment("Платёж не подтверждён платёжной системой.")

        complete_err = payment.ensure_complete()
        
        if complete_err:
            await self.payment_gateway.refund_payment(payment.uuid)
            raise exceptions.CantCompletePayment(complete_err)
        
        payment_error = await self.payment_repository.update(
            payment_uuid=payment.uuid,
            data={'status': entities.PaymentStatus.COMPLETED, 'payment_method': data.method, 'payment_date': data.date.isoformat()}, release_record=True)

        if isinstance(payment_error, (common_exceptions.PaymentNotFoundError, common_exceptions.PaymentRepositoryError)):
            await self.payment_gateway.refund_payment(payment.uuid)
            raise payment_error
        
        return None

