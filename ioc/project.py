from dishka import Provider, Scope, provide, AnyOf # type: ignore


from application.project import interactors, interfaces
from infrastructure.policy.project import policy

class ProjectProvider(Provider):

    authorization_policy = provide(
        policy.ProjectAuthorizationPolicyImpl,
        scope=Scope.REQUEST,
        provides=AnyOf[interfaces.ProjectCreateAuthorizationPolicy, interfaces.ProjectUpdateAuthorizationPolicy,
                          interfaces.ProjectGetterAuthorizationPolicy]
    )
    
    project_repository = provide(None, scope=Scope.REQUEST, provides=AnyOf[interfaces.ProjectCreator, interfaces.ProjectUpdater
                                                                           , interfaces.ProjectGetterByName, interfaces.ProjectGetterByUUID, 
                                                                           interfaces.ProjectMembersGetter, interfaces.ProjectMembersAddable])
    user_repository = provide(None, scope=Scope.REQUEST, provides=interfaces.UserGetter)
   
   

    create_project_interactor = provide(
        interactors.CreateProjectInteractor,
        scope=Scope.REQUEST,
        provides=interactors.CreateProjectInteractor,
    )
    
    update_project_interactor = provide(
        interactors.UpdateProjectInteractor,
        scope=Scope.REQUEST,
        provides=interactors.UpdateProjectInteractor,
    )
    
    get_project_interactor = provide(
        interactors.GetProjectInteractor,
        scope=Scope.REQUEST,
        provides=interactors.GetProjectInteractor,
    )
    
    add_members_to_project = provide(
        interactors.AddMembersToProjectInteractor,
        scope=Scope.REQUEST,
        provides=interactors.AddMembersToProjectInteractor,
    )