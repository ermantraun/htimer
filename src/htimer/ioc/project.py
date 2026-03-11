from dishka import Provider, Scope, provide, AnyOf, provide_all # type: ignore


from htimer.application.project import interactors, interfaces
from htimer.infrastructure.policy.project import policy

class PolicyProvider(Provider):
    project_authorization_policy = provide(
        policy.ProjectAuthorizationPolicyImpl,
        scope=Scope.REQUEST,
        provides=interfaces.ProjectAuthorizationPolicy
    )

class InteractorProvider(Provider):
    interactos = provide_all(
       interactors.CreateProjectInteractor,
       interactors.UpdateProjectInteractor,
       interactors.GetProjectInteractor,
       interactors.AddMembersToProjectInteractor,
       interactors.RemoveMembersFromProjectInteractor,
       interactors.GetProjectListInteractor,
       scope=Scope.REQUEST
       
    )

class ProjectProvider(PolicyProvider, InteractorProvider):
    pass
