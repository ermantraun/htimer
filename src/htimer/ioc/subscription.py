from dishka import Provider, Scope, provide, provide_all # type: ignore

from htimer.application.subscription import interactors, interfaces
from htimer.infrastructure.policy.subscription import policy

class PolicyProvider(Provider):
    subscription_authorization_policy = provide(
        policy.SubscriptionAuthorizationPolicyImpl,
        scope=Scope.REQUEST,
        provides=interfaces.SubscriptionAuthorizationPolicy
    )

class InteractorProvider(Provider):
    interactors = provide_all(
        interactors.CreateSubscriptionInteractor,
        interactors.UpdateSubscriptionInteractor,
        interactors.ExtendSubscriptionInteractor,
        interactors.CreatePaymentInteractor,
        interactors.CompletePaymentInteractor,
        interactors.ActivateSubscriptionInteractor,
        scope=Scope.REQUEST
    )

class SubscriptionProvider(PolicyProvider, InteractorProvider):
    pass
