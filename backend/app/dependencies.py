from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User


def get_current_user(
    db: Session = Depends(get_db)
) -> User:
    """Return the default guest user, creating it if needed."""
    user = db.query(User).filter(User.id == 1).first()
    if not user:
        user = User(
            id=1,
            email="guest@propbet.local",
            username="guest",
            hashed_password="none",
            full_name="Guest User",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user
