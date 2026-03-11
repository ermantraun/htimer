from dishka import Provider, Scope, provide, provide_all # type: ignore

from htimer.application.reports import interactors, interfaces
from htimer.infrastructure.policy.reports import policy


class PolicyProvider(Provider):
    reports_authorization_policy = provide(
        policy.ReportsAuthorizationPolicyImpl,
        scope=Scope.REQUEST,
        provides=interfaces.ReportsAuthorizationPolicy
    )


class InteractorProvider(Provider):
    interactors = provide_all(
        interactors.CreateReportRequestInteractor,
        scope=Scope.REQUEST
    )


class ReportsProvider(PolicyProvider, InteractorProvider):
    pass
