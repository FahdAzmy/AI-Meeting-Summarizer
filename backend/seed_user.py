import sys, asyncio
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv('.env')

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from src.helpers.config import settings
from src.models.user import User, UserRole
from src.models.company import Company
from src.helpers.security import hash_password

async def main():
    db_url = settings.get_database_url()
    if db_url.startswith('postgresql://'):
        db_url = db_url.replace('postgresql://', 'postgresql+asyncpg://', 1)

    engine = create_async_engine(db_url, echo=False)
    SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession)

    async with SessionLocal() as db:
        # Check if company exists
        company = Company(name="Test Company", subscription_plan="free")
        db.add(company)
        await db.flush()

        user = User(
            name="Azmy Fahd",
            email="azmyfahd66@gmail.com",
            password=hash_password("Password"),
            role=UserRole.HR,
            company_id=company.id
        )
        db.add(user)
        await db.commit()
        print("User 'azmyfahd66@gmail.com' seeded successfully with password 'Password'!")

asyncio.run(main())
