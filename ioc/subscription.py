from dishka import Provider, Scope, provide, provide_all # type: ignore

from application.subscription import interactors, interfaces
from infrastructure.policy.subscription import policy


class SubscriptionProvider(Provider):

    authorization_policy = provide(
        policy.SubscriptionAuthorizationPolicyImpl,
        scope=Scope.REQUEST,
        provides=interfaces.SubscriptionAuthorizationPolicy
    )

    payment_gateway = provide(None,
        interfaces.PaymentGateway,
        scope=Scope.REQUEST
    )
    
    interactors = provide_all(
        interactors.CreateSubscriptionInteractor,
        interactors.UpdateSubscriptionInteractor,
        interactors.ExtendSubscriptionInteractor,
        interactors.CreatePaymentInteractor,
        interactors.CompletePaymentInteractor,
        interactors.ActivateSubscriptionInteractor,
        scope=Scope.REQUEST
    )
