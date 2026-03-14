import infrastructure.policy.subscription.exceptions as exceptions

from htimer.application.subscription import interfaces
from htimer.domain import entities


class SubscriptionAuthorizationPolicyImpl(interfaces.SubscriptionAuthorizationPolicy):
    def decide_create_subscription(
        self, actor: entities.User, project: entities.Project
    ) -> exceptions.UserNotProjectCreatorError | None:
        decision = actor.decide_create_subscription(project)

        if decision is entities.UserDecisions.CreateSubscriptionDecision.ALLOWED:
            return None

        if (
            decision
            is entities.UserDecisions.CreateSubscriptionDecision.FORBIDDEN_FOR_NON_PROJECT_CREATOR
        ):
            return exceptions.UserNotProjectCreatorError(
                "Недостаточно прав: создание подписки доступно только создателю проекта."
            )

        return None

    def decide_create_payment(
        self, actor: entities.User, project: entities.Project
    ) -> exceptions.UserNotProjectCreatorError | None:
        decision = actor.decide_create_payment(project)

        if decision is entities.UserDecisions.CreatePaymentDecision.ALLOWED:
            return None

        if (
            decision
            is entities.UserDecisions.CreatePaymentDecision.FORBIDDEN_FOR_NON_PROJECT_CREATOR
        ):
            return exceptions.UserNotProjectCreatorError(
                "Недостаточно прав: создание платежа доступно только создателю проекта."
            )

        return None

    def decide_update_subscription(
        self, actor: entities.User, project: entities.Project
    ) -> exceptions.UserNotProjectCreatorError | None:
        # Use the same decision rule as creating a subscription: only project creator can cancel
        decision = actor.decide_create_subscription(project)

        if decision is entities.UserDecisions.CreateSubscriptionDecision.ALLOWED:
            return None

        if (
            decision
            is entities.UserDecisions.CreateSubscriptionDecision.FORBIDDEN_FOR_NON_PROJECT_CREATOR
        ):
            return exceptions.UserNotProjectCreatorError(
                "Недостаточно прав: изменение подписки доступно только создателю проекта."
            )

        return None
