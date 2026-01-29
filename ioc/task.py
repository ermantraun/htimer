from application.task import interactors, interfaces
from dishka import Provider, Scope, provide_all, provide  # type: ignore
from infrastructure.policy.task import policy

class TaskProvider(Provider):
    
    authorization_policy = provide(
        policy.TaskAuthorizationPolicyImpl,
        scope=Scope.REQUEST,
        provides=interfaces.TaskAuthorizationPolicy
    )

    interactors = provide_all(
        interactors.CreateTaskInteractor,
        interactors.UpdateTaskInteractor,
        interactors.DeleteTaskInteractor,
        interactors.GetTaskListInteractor,
        interactors.DeleteTaskInteractor,
        scope=Scope.REQUEST
    )


