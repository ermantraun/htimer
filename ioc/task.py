from application.task import interactors, interfaces
from dishka import Provider, Scope, provide_all, provide  # type: ignore
from infrastructure.policy.task import policy

class PolicyProvider(Provider):
    task_authorization_policy = provide(
        policy.TaskAuthorizationPolicyImpl,
        scope=Scope.REQUEST,
        provides=interfaces.TaskAuthorizationPolicy
    )

class InteractorProvider(Provider):
    interactors = provide_all(
        interactors.CreateTaskInteractor,
        interactors.UpdateTaskInteractor,
        interactors.DeleteTaskInteractor,
        interactors.GetTaskListInteractor,
        scope=Scope.REQUEST
    )

class TaskProvider(PolicyProvider, InteractorProvider):
    pass


