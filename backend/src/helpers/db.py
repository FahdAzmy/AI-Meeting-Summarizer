from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from src.helpers.config import settings
import logging

logger = logging.getLogger("app")

# Global reference to the client
client_instance = {}

async def init_db(db_name: str = None):
    logger.info("Initializing MongoDB connection …")
    client = AsyncIOMotorClient(settings.MONGO_URI)
    client_instance["client"] = client
    
    selected_db = db_name or settings.MONGO_DB
    db = client[selected_db]
    
    # If Beanie Document models exist, they should be initialized here:
    # await init_beanie(database=db, document_models=[])
    
    logger.info("MongoDB connection established")

def get_client() -> AsyncIOMotorClient:
    return client_instance.get("client")
