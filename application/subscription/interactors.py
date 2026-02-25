from uuid import uuid4, UUID
from typing import Any
from datetime import timedelta
from application import common_exceptions, common_interfaces
from domain import entities
from . import dto, interfaces, exceptions


class CreateSubscriptionInteractor:
    def __init__(
        self,
        subscription_repository: common_interfaces.SubscriptionRepository,
        user_repository: common_interfaces.UserRepository,
        project_repository: common_interfaces.ProjectRepository,
        context: common_interfaces.Context,
        clock: common_interfaces.Clock,
        authorization_policy: interfaces.SubscriptionAuthorizationPolicy,
        session: common_interfaces.DBSession,
    ):
        self.subscription_repository = subscription_repository
        self.user_repository = user_repository
        self.context = context
        self.clock = clock
        self.authorization_policy = authorization_policy
        self.project_repository = project_repository
        self.session = session
    async def execute(self, data: dto.CreateSubscriptionInDTO) -> dto.CreateSubscriptionOutDTO | common_exceptions.SubscriptionAlreadyExistsError | common_exceptions.ProjectNotFoundError | common_exceptions.InvalidTokenError | common_exceptions.UserNotFoundError | exceptions.SubscriptionAuthorizationError | exceptions.CantCreateSubscription | common_exceptions.RepositoryError:
        actor_uuid = self.context.get_current_user_uuid()
        if isinstance(actor_uuid, common_exceptions.InvalidTokenError):
            raise actor_uuid

        actor = await self.user_repository.get_by_uuid(actor_uuid)
        if isinstance(actor, (common_exceptions.UserNotFoundError, common_exceptions.RepositoryError)):
            raise actor

        project = await self.project_repository.get_by_uuid(data.project_uuid)
        if isinstance(project, (common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError)):
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
            created_at=await self.clock.now_date(),
        )

        ensure_err = new_subscription.ensure_create()
        if ensure_err:
            raise exceptions.CantCreateSubscription(ensure_err)

        created_subscription = await self.subscription_repository.create(new_subscription)
        if isinstance(created_subscription, (common_exceptions.SubscriptionAlreadyExistsError, common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError)):
            raise created_subscription
        await self.session.commit()
        return dto.CreateSubscriptionOutDTO(created_subscription)

class UpdateSubscriptionInteractor:
    def __init__(
        self,
        session: common_interfaces.DBSession,
        subscription_repository: common_interfaces.SubscriptionRepository,
        user_repository: common_interfaces.UserRepository,
        project_repository: common_interfaces.ProjectRepository,
        context: common_interfaces.Context,
        clock: common_interfaces.Clock,
        authorization_policy: interfaces.SubscriptionAuthorizationPolicy,
    ):
        self.subscription_repository = subscription_repository
        self.user_repository = user_repository
        self.project_repository = project_repository
        self.context = context
        self.clock = clock
        self.authorization_policy = authorization_policy
        self.session = session

    async def execute(self, data: dto.UpdateSubscriptionInDTO) -> None | common_exceptions.SubscriptionNotFoundError | common_exceptions.ProjectNotFoundError | common_exceptions.InvalidTokenError | common_exceptions.UserNotFoundError | exceptions.SubscriptionAuthorizationError | exceptions.CantUpdateSubscription | common_exceptions.RepositoryError:

        actor_uuid = self.context.get_current_user_uuid()
        if isinstance(actor_uuid, common_exceptions.InvalidTokenError):
            raise actor_uuid

        actor = await self.user_repository.get_by_uuid(actor_uuid)
        if isinstance(actor, (common_exceptions.UserNotFoundError, common_exceptions.RepositoryError)):
            raise actor

        project = await self.project_repository.get_by_uuid(data.project_uuid)
        if isinstance(project, (common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError)):
            raise project

        auth_err = self.authorization_policy.decide_update_subscription(actor=actor, project=project)
        if auth_err is not None:
            raise auth_err

        subscription = await self.project_repository.get_current_subscription(data.project_uuid)
        if isinstance(subscription, (common_exceptions.SubscriptionNotFoundError, common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError)):
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

        if isinstance(update_result, (common_exceptions.SubscriptionNotFoundError, common_exceptions.RepositoryError)):
            raise update_result

        await self.session.commit()

        return None


class ExtendSubscriptionInteractor:
    def __init__(
        self,
        subscription_repository: common_interfaces.SubscriptionRepository,
        project_repository: common_interfaces.ProjectRepository,
        payment_repository: common_interfaces.PaymentRepository,
        payment_gateway: common_interfaces.PaymentGateway,
        clock: common_interfaces.Clock,
        session: common_interfaces.DBSession,
    ):
        self.subscription_repository = subscription_repository
        self.project_repository = project_repository
        self.clock = clock
        self.payment_repository = payment_repository
        self.payment_gateway = payment_gateway
        self.session = session
    async def execute(self, data: dto.ExtendSubscriptionInDTO) -> None | common_exceptions.SubscriptionNotFoundError | common_exceptions.ProjectNotFoundError | exceptions.CantExtendSubscription | common_exceptions.PaymentNotFoundError | common_exceptions.PaymentNotComplete | common_exceptions.PaymentNotExistsError | common_exceptions.RepositoryError:

        project = await self.project_repository.get_by_uuid(data.project_uuid)
        if isinstance(project, (common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError)):
            raise project

        subscription = await self.subscription_repository.get_by_project_uuid(data.project_uuid, lock_record=True)
        if isinstance(subscription, (common_exceptions.SubscriptionNotFoundError, common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError)):
            raise subscription

        payment = await self.payment_repository.get_by_uuid(data.payment_uuid)
        
        if isinstance(payment, (common_exceptions.PaymentNotFoundError, common_exceptions.RepositoryError)):
            raise payment
        
        gateway_payment_id = await self.payment_repository.get_gateway_payment_id(payment.uuid)
        if isinstance(gateway_payment_id, (common_exceptions.PaymentNotFoundError, common_exceptions.RepositoryError)):
            raise gateway_payment_id

        applied_to_subscription = await self.payment_repository.payment_applied_to_subscription(payment.uuid)
        if isinstance(applied_to_subscription, (common_exceptions.PaymentNotFoundError, common_exceptions.RepositoryError)):
            raise applied_to_subscription
        if applied_to_subscription:
            return None

        verify = await self.payment_gateway.verify_payment_complete(gateway_payment_id)
        
        if isinstance(verify, common_exceptions.PaymentNotComplete) or isinstance(verify, common_exceptions.PaymentNotExistsError):
            raise verify
        
        ensure_res = subscription.ensure_extend()

        if ensure_res:
            raise exceptions.CantExtendSubscription(ensure_res)
        
        update_data: dict[str, Any] = {'status': entities.SubscriptionStatus.ACTIVE}


        if payment.complete_date is not None:
            update_data['end_date'] = await self.clock.now_date() + timedelta(30)
        else:
            raise exceptions.CantExtendSubscription("Платёж не завершён, невозможно продлить подписку.")
            

        update_res = await self.subscription_repository.update(
            subscription_uuid=subscription.uuid,
            data=update_data
        )

        if isinstance(update_res, (common_exceptions.SubscriptionNotFoundError, common_exceptions.RepositoryError)):
            raise update_res
        
        update_payment_res = await self.payment_repository.update(
            payment_uuid=payment.uuid,
            data={'applied_to_subscription': True}
        )
        if isinstance(update_payment_res, (common_exceptions.PaymentNotFoundError, common_exceptions.RepositoryError)):
            raise update_payment_res

        await self.session.commit()
        return None
    
class ActivateSubscriptionInteractor:
    def __init__(
        self,
        subscription_repository: common_interfaces.SubscriptionRepository,
        project_repository: common_interfaces.ProjectRepository,
        clock: common_interfaces.Clock,
        session: common_interfaces.DBSession,
        payment_repository: common_interfaces.PaymentRepository,
        payment_gateway: common_interfaces.PaymentGateway,

    ):
        self.subscription_repository = subscription_repository
        self.project_repository = project_repository
        self.clock = clock
        self.session = session
        self.payment_repository = payment_repository
        self.payment_gateway = payment_gateway

    async def execute(self, data: dto.ActivateSubscriptionInDTO) -> None | common_exceptions.SubscriptionNotFoundError | common_exceptions.ProjectNotFoundError | exceptions.CantActivateSubscription | common_exceptions.PaymentNotFoundError | common_exceptions.PaymentNotComplete | common_exceptions.PaymentNotExistsError | common_exceptions.RepositoryError:



        project = await self.project_repository.get_by_uuid(data.project_uuid)
        if isinstance(project, (common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError)):
            raise project

        subscription = await self.subscription_repository.get_by_project_uuid(data.project_uuid, lock_record=True)
        if isinstance(subscription, (common_exceptions.SubscriptionNotFoundError, common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError)):
            raise subscription

        payment = await self.payment_repository.get_by_uuid(data.payment_uuid)
        if isinstance(payment, (common_exceptions.PaymentNotFoundError, common_exceptions.RepositoryError)):
            raise payment
        
        gateway_payment_id = await self.payment_repository.get_gateway_payment_id(payment.uuid)
        if isinstance(gateway_payment_id, (common_exceptions.PaymentNotFoundError, common_exceptions.RepositoryError)):
            raise gateway_payment_id
        
        applied_to_subscription = await self.payment_repository.payment_applied_to_subscription(payment.uuid)
        if isinstance(applied_to_subscription, (common_exceptions.PaymentNotFoundError, common_exceptions.RepositoryError)):
            raise applied_to_subscription
        if applied_to_subscription:
            return None

        verify = await self.payment_gateway.verify_payment_complete(gateway_payment_id)
        if isinstance(verify, common_exceptions.PaymentNotComplete) or isinstance(verify, common_exceptions.PaymentNotExistsError):
            raise verify

        ensure_res = subscription.ensure_activate()

        if ensure_res:
            raise exceptions.CantActivateSubscription(ensure_res)
        
        update_res = await self.subscription_repository.update(
            subscription_uuid=subscription.uuid,
            data={'status': entities.SubscriptionStatus.ACTIVE,
                  'start_date': await self.clock.now_date(),
                  'end_date': await self.clock.now_date() + timedelta(30)}
        )

        if isinstance(update_res, (common_exceptions.SubscriptionNotFoundError, common_exceptions.RepositoryError)):
            raise update_res
        
        update_payment_res = await self.payment_repository.update(
            payment_uuid=payment.uuid,
            data={'applied_to_subscription': True}
        )
        if isinstance(update_payment_res, (common_exceptions.PaymentNotFoundError, common_exceptions.RepositoryError)):
            raise update_payment_res

        await self.session.commit()
        return None
    
class CreatePaymentInteractor:
    def __init__(
        self,
        subscription_repository: common_interfaces.SubscriptionRepository,
        payment_repository: common_interfaces.PaymentRepository,
        user_repository: common_interfaces.UserRepository,
        project_repository: common_interfaces.ProjectRepository,
        context: common_interfaces.Context,
        clock: common_interfaces.Clock,
        authorization_policy: interfaces.SubscriptionAuthorizationPolicy,
        payment_gateway: common_interfaces.PaymentGateway,
        session: common_interfaces.DBSession,
    ):
        self.subscription_repository = subscription_repository
        self.user_repository = user_repository
        self.context = context
        self.clock = clock
        self.authorization_policy = authorization_policy
        self.project_repository = project_repository
        self.payment_repository = payment_repository
        self.payment_gateway = payment_gateway
        self.session = session
    async def execute(self, data: dto.CreatePaymentInDTO) -> dto.CreatePaymentOutDTO | common_exceptions.SubscriptionNotFoundError | common_exceptions.ProjectNotFoundError | common_exceptions.InvalidTokenError | common_exceptions.UserNotFoundError | exceptions.SubscriptionAuthorizationError | exceptions.CantCreateSubscription | common_exceptions.PaymentFailedError | exceptions.CantCreatePayment | common_exceptions.RepositoryError:
        actor_uuid = self.context.get_current_user_uuid()
        if isinstance(actor_uuid, common_exceptions.InvalidTokenError):
            raise actor_uuid

        actor = await self.user_repository.get_by_uuid(actor_uuid)
        if isinstance(actor, (common_exceptions.UserNotFoundError, common_exceptions.RepositoryError)):
            raise actor

        project = await self.project_repository.get_by_uuid(data.project_uuid)
        if isinstance(project, (common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError)):
            raise project


        authorization_error = self.authorization_policy.decide_create_payment(
            actor=actor,
            project=project,

        )
        if authorization_error is not None:
            raise authorization_error

        subscription = await self.subscription_repository.get_by_project_uuid(data.project_uuid)
        if isinstance(subscription, (common_exceptions.SubscriptionNotFoundError, common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError)):
            raise subscription

        payment = entities.Payment(
            uuid=uuid4(),
            subscription=subscription,
            amount=entities.value_objects.MoneyAmount(amount=data.amount, currency=entities.value_objects.CurrencyEnum(data.currency)),
            created_at=await self.clock.now_date(),
        )

        ensure_err = payment.ensure_create()
        if ensure_err:
            raise exceptions.CantCreatePayment(ensure_err)

        payment =  await self.payment_repository.create(payment)
        
        if isinstance(payment, (common_exceptions.SubscriptionNotFoundError, common_exceptions.RepositoryError)):
            raise payment
        
        gateway_payment: tuple[str, UUID] | common_exceptions.PaymentFailedError = await self.payment_gateway.create_payment(
            actor=actor,
            project=project,
            amount=data.amount,
            payment=payment
        )
        
        if isinstance(gateway_payment, common_exceptions.PaymentFailedError):
            raise gateway_payment

        await self.payment_repository.update(
            payment_uuid=payment.uuid,
            data={'gateway_payment_id': str(gateway_payment[1])})

        await self.session.commit()

        return dto.CreatePaymentOutDTO(gateway_payment[0])
    
    
class CompletePaymentInteractor:
    def __init__(
        self,
        payment_repository: common_interfaces.PaymentRepository,
        user_repository: common_interfaces.UserRepository,
        project_repository: common_interfaces.ProjectRepository,
        clock: common_interfaces.Clock,
        payment_gateway: common_interfaces.PaymentGateway,
        session: common_interfaces.DBSession,
    ):
        self.user_repository = user_repository
        self.clock = clock
        self.project_repository = project_repository
        self.payment_repository = payment_repository
        self.payment_gateway = payment_gateway
        self.session = session


    async def execute(self, data: dto.CompletePaymentInDTO) -> None | common_exceptions.SubscriptionNotFoundError | common_exceptions.ProjectNotFoundError | common_exceptions.PaymentNotFoundError | exceptions.CantCompletePayment | common_exceptions.PaymentNotComplete | common_exceptions.PaymentNotExistsError | common_exceptions.RepositoryError:
        
        

        gateway_payment_id = await self.payment_repository.get_gateway_payment_id(data.payment_uuid)
        if isinstance(gateway_payment_id, (common_exceptions.PaymentNotFoundError, common_exceptions.RepositoryError)):
            raise gateway_payment_id

        is_verified = await self.payment_gateway.verify_payment_complete(gateway_payment_id)
        if isinstance(is_verified, common_exceptions.PaymentNotComplete) or isinstance(is_verified, common_exceptions.PaymentNotExistsError):
            raise is_verified

        if not is_verified:
            raise exceptions.CantCompletePayment("Платёж не подтверждён платёжной системой.")

        payment = await self.payment_repository.get_by_uuid(data.payment_uuid, lock_record=True)
        if isinstance(payment, (common_exceptions.PaymentNotFoundError, common_exceptions.RepositoryError)):
            raise payment

        complete_err = payment.ensure_complete()
        
        if complete_err:
            await self.payment_gateway.refund_payment(payment, gateway_payment_id)
            raise exceptions.CantCompletePayment(complete_err)
        
        payment_error = await self.payment_repository.update(
            payment_uuid=payment.uuid,
            data={'status': entities.PaymentStatus.COMPLETED})

        if isinstance(payment_error, (common_exceptions.PaymentNotFoundError, common_exceptions.RepositoryError)):
            raise payment_error
        
        await self.session.commit()
        return None

class CompletePaymentAndUpdateSubscriptionInteractor:
    def __init__(
        self,
        subscription_repository: common_interfaces.SubscriptionRepository,
        payment_repository: common_interfaces.PaymentRepository,
        user_repository: common_interfaces.UserRepository,
        project_repository: common_interfaces.ProjectRepository,
        clock: common_interfaces.Clock,
        payment_gateway: common_interfaces.PaymentGateway,
        session: common_interfaces.DBSession,
    ):
        self.subscription_repository = subscription_repository
        self.user_repository = user_repository
        self.clock = clock
        self.project_repository = project_repository
        self.payment_repository = payment_repository
        self.payment_gateway = payment_gateway
        self.session = session

    async def execute(self, data: dto.CompletePaymentAndUpdateSubscriptionInDTO) -> None | exceptions.CantActivateSubscription | common_exceptions.SubscriptionNotFoundError | common_exceptions.ProjectNotFoundError | common_exceptions.PaymentNotFoundError | exceptions.CantCompletePayment | common_exceptions.PaymentNotComplete | common_exceptions.PaymentNotExistsError | exceptions.CantExtendSubscription | common_exceptions.RepositoryError:
        
        complete_payment_result = await CompletePaymentInteractor(
            payment_repository=self.payment_repository,
            user_repository=self.user_repository,
            project_repository=self.project_repository,
            clock=self.clock,
            payment_gateway=self.payment_gateway,
            session=self.session,
        ).execute(dto.CompletePaymentInDTO(payment_uuid=data.payment_uuid))
            

        if complete_payment_result is not None:
            raise complete_payment_result

        subscription = await self.subscription_repository.get_by_project_uuid(data.project_uuid)
        if isinstance(subscription, (common_exceptions.SubscriptionNotFoundError, common_exceptions.ProjectNotFoundError, common_exceptions.RepositoryError)):
            raise subscription
        
        extend_ensure_res = subscription.ensure_extend()

        if extend_ensure_res:
            raise exceptions.CantExtendSubscription(extend_ensure_res)
        else:
            extend_subscription_result = await ExtendSubscriptionInteractor(
                subscription_repository=self.subscription_repository,
                project_repository=self.project_repository,
                payment_repository=self.payment_repository,
                payment_gateway=self.payment_gateway,
                clock=self.clock,
                session=self.session,
            ).execute(dto.ExtendSubscriptionInDTO(project_uuid=data.project_uuid, payment_uuid=data.payment_uuid))

            if extend_subscription_result is not None:
                raise extend_subscription_result

        ensure_activate_res = subscription.ensure_activate()

        if ensure_activate_res:
            raise exceptions.CantActivateSubscription(ensure_activate_res)
        else: 
            activate_subscription_result = await ActivateSubscriptionInteractor(
                    subscription_repository=self.subscription_repository,
                    project_repository=self.project_repository,
                    clock=self.clock,
                    session=self.session,
                    payment_repository=self.payment_repository,
                    payment_gateway=self.payment_gateway,
                ).execute(dto.ActivateSubscriptionInDTO(project_uuid=data.project_uuid, payment_uuid=data.payment_uuid))

            if activate_subscription_result is not None:
                    raise activate_subscription_result

        return None
