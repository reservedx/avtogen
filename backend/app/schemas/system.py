from pydantic import BaseModel

from app.schemas.auth import AuthSessionRead
from app.schemas.article import MetricsRead, SettingsSummaryRead
from app.schemas.research import LaunchReadinessRead


class SystemOverviewRead(BaseModel):
    settings: SettingsSummaryRead
    metrics: MetricsRead
    readiness: LaunchReadinessRead
    session: AuthSessionRead
