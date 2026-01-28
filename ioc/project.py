from dishka import Provider, Scope, provide, AnyOf, provide_all # type: ignore


from application.project import interactors, interfaces
from infrastructure.policy.project import policy

class ProjectProvider(Provider):

    authorization_policy = provide(
        policy.ProjectAuthorizationPolicyImpl,
        scope=Scope.REQUEST,
        provides=interfaces.ProjectAuthorizationPolicy
    )


    
    interactos = provide_all(
       interactors.CreateProjectInteractor,
       interactors.UpdateProjectInteractor,
       interactors.GetProjectInteractor,
       interactors.AddMembersToProjectInteractor,
       interactors.RemoveMembersFromProjectInteractor,
       interactors.GetProjectListInteractor,
       scope=Scope.REQUEST
       
    )