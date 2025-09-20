from sqlalchemy.orm import Session
from .models import User, Ad
from typing import List, Optional

def get_or_create_user(db: Session, telegram_id: int, username: str = None, full_name: str = None) -> User:
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        user = User(
            telegram_id=telegram_id,
            username=username,
            full_name=full_name
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

def get_user_ads(db: Session, user_id: int) -> List[Ad]:
    return db.query(Ad).filter(Ad.user_id == user_id).order_by(Ad.created_at.desc()).all()

def create_ad(db: Session, user_id: int, channel: str, text: str, price: int, duration: str) -> Ad:
    ad = Ad(
        user_id=user_id,
        channel=channel,
        text=text,
        price=price,
        duration=duration
    )
    db.add(ad)
    db.commit()
    db.refresh(ad)
    return ad