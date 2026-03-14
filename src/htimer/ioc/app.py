from __future__ import annotations

from .common import CommonProvider
from .daily_log import DailyLogProvider
from .project import ProjectProvider
from .reports import ReportsProvider
from .stage import StageProvider
from .subscription import SubscriptionProvider
from .task import TaskProvider
from .user import UserProvider


class AppProvider(
    CommonProvider,
    UserProvider,
    ProjectProvider,
    StageProvider,
    DailyLogProvider,
    TaskProvider,
    SubscriptionProvider,
    ReportsProvider,
):
    pass
