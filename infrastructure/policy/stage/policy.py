from domain import entities
from application.stage import interfaces
import exceptions # type: ignore

class StageAuthorizationPolicyImpl(interfaces.StageCreateAuthorizationPolicy, interfaces.StageUpdateAuthorizationPolicy):
    
    def can_create_stage(
        self, actor: entities.User, project: entities.Project, project_members: list[entities.User], 
    ) -> interfaces.exceptions.StageAuthorizationError | None:
       
        actor_decision = actor.decide_create_stage(project, project_members)
        
        if actor_decision is entities.UserDecisions.CreateStageDecision.ALLOWED:
            return None
        
        if actor_decision is entities.UserDecisions.CreateStageDecision.FORBIDDEN_FOR_NON_MEMBER:
            return exceptions.UserNotProjectMemberError(
                "Пользователь не является участником проекта и не может создать этап."
            )
   
    def can_update_stage(self, actor: entities.User, project: entities.Project, project_members: list[entities.User],
   ) -> exceptions.UserNotProjectMemberError | None:
         
         actor_decision = actor.decide_update_stage(project, project_members)
         
         if actor_decision is entities.UserDecisions.UpdateStageDecision.ALLOWED:
              return None
         
         if actor_decision is entities.UserDecisions.UpdateStageDecision.FORBIDDEN_FOR_NON_MEMBER:
              return exceptions.UserNotProjectMemberError(
                "Пользователь не является участником проекта и не может обновить этап."
              )
         
         return None