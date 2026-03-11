from dishka import Provider, Scope, provide_all, AnyOf, provide # type: ignore


from htimer.application.daily_log import interactors, interfaces
from htimer.infrastructure.policy.daily_log import policy

class PolicyProvider(Provider):
    daily_log_authorization_policy = provide(
        policy.DailyLogAuthorizationPolicy,
        scope=Scope.REQUEST,
        provides=interfaces.DailyLogAuthorizationPolicy
    )

class InteractorProvider(Provider):
    interactors = provide_all(
        interactors.CreateDailyLogInteractor,
        interactors.UpdateDailyLogInteractor,
        interactors.GetDailyLogInteractor,
        interactors.GetDailyLogListInteractor,
        interactors.CreateDailyLogFileInteractor,
        interactors.GetDailyLogFileInteractor,
        interactors.RemoveDailyLogFileInteractor,
        interactors.GetDailyLogFileListInteractor,
        scope=Scope.REQUEST,
    )

class DailyLogProvider(PolicyProvider, InteractorProvider):
    pass
