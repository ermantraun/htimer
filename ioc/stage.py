from dishka import Provider, Scope, provide, AnyOf, provide_all # type: ignore
from application.stage import interactors, interfaces
from infrastructure.policy.stage import policy

class PolicyProvider(Provider):
    stage_authorization_policy = provide(
        policy.StageAuthorizationPolicyImpl,
        scope=Scope.REQUEST,
        provides=interfaces.StageAuthorizationPolicy
    )

class InteractorProvider(Provider):
    interactors = provide_all(
        interactors.CreateStageInteractor,
        interactors.UpdateStageInteractor,
        interactors.DeleteStageInteractor,
        interactors.GetStageListInteractor,
        scope=Scope.REQUEST
    )

class StageProvider(PolicyProvider, InteractorProvider):
    pass
