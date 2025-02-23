from motor.motor_asyncio import AsyncIOMotorClient
from typing import Dict, Any, Optional
import logging
from datetime import datetime
from ..error_handling import ValidationError

class DatabaseClient:
    """MongoDB database client."""
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger("movie_generator.db")
        self.config = config
        
        # Initialize client
        self.client = AsyncIOMotorClient(config["mongodb_uri"])
        self.db = self.client[config["database_name"]]
        
        # Collections
        self.users = self.db.users
        self.projects = self.db.projects
        self.backups = self.db.backups
        
        # Indexes
        self._setup_indexes()
    
    async def _setup_indexes(self):
        """Setup database indexes."""
        try:
            # User indexes
            await self.users.create_index("email", unique=True)
            await self.users.create_index("username", unique=True)
            
            # Project indexes
            await self.projects.create_index([
                ("user_id", 1),
                ("created_at", -1)
            ])
            
            # Backup indexes
            await self.backups.create_index([
                ("project_id", 1),
                ("created_at", -1)
            ])
            
        except Exception as e:
            self.logger.error(f"Failed to setup indexes: {str(e)}")
            raise
    
    async def close(self):
        """Close database connection."""
        self.client.close() 