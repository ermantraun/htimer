
from __future__ import annotations

from .daily_log import DailyLogProvider
from .project import ProjectProvider
from .user import UserProvider
from .common import CommonProvider
from .stage import StageProvider
from .subscription import SubscriptionProvider
from .task import TaskProvider


class AppProvider(CommonProvider, UserProvider, ProjectProvider, StageProvider, DailyLogProvider, TaskProvider, SubscriptionProvider):
    pass