from dishka import Provider, Scope, provide_all, AnyOf, provide # type: ignore


from application.daily_log import interactors, interfaces
from infrastructure.policy.daily_log import policy


class DailyLogProvider(Provider):
    
    policy = provide(policy.DailyLogAuthorizationPolicy, scope=Scope.REQUEST, provides=interfaces.DailyLogAuthorizationPolicy)
    
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
    
    