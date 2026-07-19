from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...db.session import get_db
from ...models import Dataset, User, UserSession, UserWallet
from ...schemas.research import DatasetResponse
from ..dependencies import get_current_identity


router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("", response_model=list[DatasetResponse])
def list_datasets(
    db: Session = Depends(get_db),
    identity: tuple[User, UserWallet, UserSession] = Depends(get_current_identity),
) -> list[Dataset]:
    user, _, _ = identity
    return list(db.scalars(select(Dataset).where(Dataset.owner_id == user.id)).all())
