from dishka import Provider, Scope, provide, AnyOf # type: ignore
from application.stage import interactors, interfaces
from infrastructure.policy.stage import policy


class StageProvider(Provider):
    
    authorization_policy = provide(
        policy.StageAuthorizationPolicyImpl,
        scope=Scope.REQUEST,
        provides=AnyOf[interfaces.StageCreateAuthorizationPolicy]
    )

    create_stage_interactor = provide(
        interactors.CreateStageInteractor,
        scope=Scope.REQUEST,
        provides=interactors.CreateStageInteractor,
    )