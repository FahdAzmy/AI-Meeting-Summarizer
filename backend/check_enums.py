import sys, asyncio
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv('.env')
from src.helpers.config import settings
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    db_url = settings.get_database_url()
    if db_url.startswith('postgresql://'):
        db_url = db_url.replace('postgresql://', 'postgresql+asyncpg://', 1)

    engine = create_async_engine(db_url, echo=False)
    async with engine.connect() as conn:
        try:
            r1 = await conn.execute(text("SELECT unnest(enum_range(NULL::userrole))::text AS v"))
            print("userrole values:", [row[0] for row in r1])
        except Exception as e:
            print(f"userrole error: {e}")
        try:
            r2 = await conn.execute(text("SELECT unnest(enum_range(NULL::meetingstatus))::text AS v"))
            print("meetingstatus values:", [row[0] for row in r2])
        except Exception as e:
            print(f"meetingstatus error: {e}")

asyncio.run(main())
