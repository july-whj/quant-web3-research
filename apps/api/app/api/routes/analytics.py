from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from ...db.session import get_db
from ...models import LoginEvent, User, UserWallet
from ...schemas.research import UsageSummary
from ..dependencies import require_admin_key


router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/usage", response_model=UsageSummary, dependencies=[Depends(require_admin_key)])
def usage(db: Session = Depends(get_db)) -> UsageSummary:
    now = datetime.now(UTC)
    users = db.scalar(select(func.count(User.id))) or 0
    wallets = db.scalar(select(func.count(UserWallet.id))) or 0
    dau = db.scalar(
        select(func.count(distinct(LoginEvent.user_id))).where(LoginEvent.created_at >= now - timedelta(days=1))
    ) or 0
    mau = db.scalar(
        select(func.count(distinct(LoginEvent.user_id))).where(LoginEvent.created_at >= now - timedelta(days=30))
    ) or 0
    return UsageSummary(users=users, wallets=wallets, daily_active_users=dau, monthly_active_users=mau)
