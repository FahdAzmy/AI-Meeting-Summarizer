from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie, PydanticObjectId as BeaniePydanticObjectId
from src.helpers.config import settings
import logging
import os
from typing import AsyncGenerator, Any
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

logger = logging.getLogger("app")

# Global reference to database clients/sessions
client_instance = {}
postgres_engine = None
SessionLocal = None

# Custom PydanticObjectId helper to route depending on DB mode
DATABASE_TYPE = os.getenv("DATABASE_TYPE", "postgres").lower()

if DATABASE_TYPE == "mongodb":
    PydanticObjectId = BeaniePydanticObjectId
else:
    # In PostgreSQL mode, IDs can be string UUIDs or any string.
    # We define a custom string bypass class to avoid PydanticObjectId validation errors on the routes.
    class PydanticObjectId(str):
        @classmethod
        def __get_validators__(cls):
            yield cls.validate
            
        @classmethod
        def validate(cls, v):
            return str(v)

async def init_db(db_name: str = None):
    db_type = getattr(settings, "DATABASE_TYPE", "postgres").lower()
    
    if db_type == "postgres":
        logger.info("Initializing PostgreSQL connection …")
        global postgres_engine, SessionLocal
        
        db_url = settings.get_database_url()
        # Ensure it has the asyncpg prefix
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
            
        postgres_engine = create_async_engine(
            db_url,
            echo=False,
            future=True,
        )
        SessionLocal = async_sessionmaker(
            bind=postgres_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        
        # Create database tables if they do not exist
        from src.models.meeting import Base
        async with postgres_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
        logger.info("PostgreSQL connection established and tables verified")
    else:
        logger.info("Initializing MongoDB connection …")
        client = AsyncIOMotorClient(settings.MONGO_URI)
        client_instance["client"] = client
        
        selected_db = db_name or settings.MONGO_DB
        db = client[selected_db]
        
        # Initialize Beanie Document models
        from src.models.meeting import Meeting
        await init_beanie(database=db, document_models=[Meeting])
        
        logger.info("MongoDB connection established")

def get_client() -> AsyncIOMotorClient:
    return client_instance.get("client")

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get a PostgreSQL database session."""
    if SessionLocal is None:
        raise RuntimeError("PostgreSQL SessionLocal is not initialized.")
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
