"""Seed demo users and sample trades."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.stock import Stock
from app.models.user import Account, User
from app.services.order_engine import place_order


async def get_or_create_user(db, email, name, role):
    res = await db.execute(select(User).where(User.email == email))
    user = res.scalar_one_or_none()
    if user:
        return user
    user = User(email=email, password_hash=hash_password("password123"), full_name=name, role=role)
    db.add(user)
    await db.flush()
    db.add(Account(user_id=user.id))
    await db.commit()
    await db.refresh(user)
    return user


async def seed():
    async with AsyncSessionLocal() as db:
        demo = await get_or_create_user(db, "demo@demo.com", "Demo User", "user")
        admin = await get_or_create_user(db, "admin@demo.com", "Admin User", "admin")

        # seed some trades for demo user
        for symbol, qty in [("RELIANCE", 10), ("TCS", 5), ("INFY", 8)]:
            stock_res = await db.execute(select(Stock).where(Stock.symbol == symbol))
            stock = stock_res.scalar_one_or_none()
            if stock:
                await place_order(db, user_id=demo.id, stock=stock, side="BUY", order_type="MARKET", quantity=qty)
        print("Demo user and admin seeded with sample trades.")

asyncio.run(seed())
