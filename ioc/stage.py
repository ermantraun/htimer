from dishka import Provider, Scope, provide, AnyOf, provide_all # type: ignore
from application.stage import interactors, interfaces
from infrastructure.policy.stage import policy


class StageProvider(Provider):
    
    authorization_policy = provide(
        policy.StageAuthorizationPolicyImpl,
        scope=Scope.REQUEST,
        provides=interfaces.StageAuthorizationPolicy
    )

    
    interactors = provide_all(
        interactors.CreateStageInteractor,
        interactors.UpdateStageInteractor,
        interactors.DeleteStageInteractor,
        interactors.GetStageListInteractor,
        scope=Scope.REQUEST
    )