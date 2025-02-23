from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import jwt
import bcrypt
import logging
from uuid import uuid4
from .models import UserInDB, UserCreate, Token, UserUpdate
from ..error_handling import ValidationError, ResourceNotFoundError

class AuthService:
    """Authentication and user management service."""
    
    def __init__(self, db_client, config: Dict[str, Any]):
        self.logger = logging.getLogger("movie_generator.auth")
        self.db = db_client
        self.config = config
        
        # Token settings
        self.token_settings = {
            "secret_key": config["secret_key"],
            "algorithm": "HS256",
            "access_token_expire_minutes": 30,
            "refresh_token_expire_days": 7
        }
        
        # Password settings
        self.password_settings = {
            "salt_rounds": 12
        }
    
    async def create_user(self, user_data: UserCreate) -> UserInDB:
        """Create new user."""
        try:
            # Check if user exists
            if await self._get_user_by_email(user_data.email):
                raise ValidationError("Email already registered")
            
            # Hash password
            hashed_password = self._hash_password(user_data.password)
            
            # Create user document
            user_doc = {
                "id": str(uuid4()),
                "email": user_data.email,
                "username": user_data.username,
                "full_name": user_data.full_name,
                "hashed_password": hashed_password,
                "is_active": True,
                "tier": "free_tier",
                "scopes": ["read"],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Save to database
            await self.db.users.insert_one(user_doc)
            
            return UserInDB(**user_doc)
            
        except Exception as e:
            self.logger.error(f"User creation failed: {str(e)}")
            raise
    
    async def authenticate_user(self, email: str, password: str) -> Token:
        """Authenticate user and return token."""
        try:
            # Get user
            user = await self._get_user_by_email(email)
            if not user:
                raise ValidationError("Invalid credentials")
            
            # Verify password
            if not self._verify_password(password, user.hashed_password):
                raise ValidationError("Invalid credentials")
            
            # Generate tokens
            access_token = self._create_access_token(user)
            refresh_token = self._create_refresh_token(user)
            
            return Token(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=datetime.utcnow() + timedelta(minutes=self.token_settings["access_token_expire_minutes"])
            )
            
        except Exception as e:
            self.logger.error(f"Authentication failed: {str(e)}")
            raise
    
    async def refresh_token(self, refresh_token: str) -> Token:
        """Refresh access token using refresh token."""
        try:
            # Verify refresh token
            payload = jwt.decode(
                refresh_token,
                self.token_settings["secret_key"],
                algorithms=[self.token_settings["algorithm"]]
            )
            
            # Get user
            user = await self._get_user_by_id(payload["sub"])
            if not user:
                raise ValidationError("Invalid refresh token")
            
            # Generate new access token
            access_token = self._create_access_token(user)
            
            return Token(
                access_token=access_token,
                expires_at=datetime.utcnow() + timedelta(minutes=self.token_settings["access_token_expire_minutes"])
            )
            
        except jwt.PyJWTError:
            raise ValidationError("Invalid refresh token")
        except Exception as e:
            self.logger.error(f"Token refresh failed: {str(e)}")
            raise
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        salt = bcrypt.gensalt(rounds=self.password_settings["salt_rounds"])
        return bcrypt.hashpw(password.encode(), salt).decode()
    
    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return bcrypt.checkpw(
            plain_password.encode(),
            hashed_password.encode()
        )
    
    def _create_access_token(self, user: UserInDB) -> str:
        """Create JWT access token."""
        expires_delta = timedelta(minutes=self.token_settings["access_token_expire_minutes"])
        expires_at = datetime.utcnow() + expires_delta
        
        to_encode = {
            "sub": user.id,
            "exp": expires_at,
            "scopes": user.scopes,
            "tier": user.tier
        }
        
        return jwt.encode(
            to_encode,
            self.token_settings["secret_key"],
            algorithm=self.token_settings["algorithm"]
        )
    
    def _create_refresh_token(self, user: UserInDB) -> str:
        """Create JWT refresh token."""
        expires_delta = timedelta(days=self.token_settings["refresh_token_expire_days"])
        expires_at = datetime.utcnow() + expires_delta
        
        to_encode = {
            "sub": user.id,
            "exp": expires_at,
            "type": "refresh"
        }
        
        return jwt.encode(
            to_encode,
            self.token_settings["secret_key"],
            algorithm=self.token_settings["algorithm"]
        )
    
    async def _get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """Get user by email."""
        user_doc = await self.db.users.find_one({"email": email})
        return UserInDB(**user_doc) if user_doc else None
    
    async def _get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        """Get user by ID."""
        user_doc = await self.db.users.find_one({"id": user_id})
        return UserInDB(**user_doc) if user_doc else None
    
    async def update_user(self, user_id: str, update_data: UserUpdate) -> UserInDB:
        """Update user profile."""
        try:
            # Get current user
            user = await self._get_user_by_id(user_id)
            if not user:
                raise ResourceNotFoundError("User", user_id)
            
            # Prepare update document
            update_doc = {}
            if update_data.email:
                # Check if email is already taken
                existing = await self._get_user_by_email(update_data.email)
                if existing and existing.id != user_id:
                    raise ValidationError("Email already registered")
                update_doc["email"] = update_data.email
            
            if update_data.full_name:
                update_doc["full_name"] = update_data.full_name
            
            if update_data.password:
                update_doc["hashed_password"] = self._hash_password(update_data.password)
            
            if update_data.tier:
                update_doc["tier"] = update_data.tier
            
            if update_data.scopes:
                update_doc["scopes"] = update_data.scopes
            
            update_doc["updated_at"] = datetime.utcnow()
            
            # Update user
            await self.db.users.update_one(
                {"id": user_id},
                {"$set": update_doc}
            )
            
            # Get updated user
            updated_user = await self._get_user_by_id(user_id)
            if not updated_user:
                raise ResourceNotFoundError("User", user_id)
            
            return updated_user
            
        except Exception as e:
            self.logger.error(f"User update failed: {str(e)}")
            raise
    
    async def get_user_projects(self, user_id: str) -> List[Dict]:
        """Get user's projects."""
        try:
            cursor = self.db.projects.find({"user_id": user_id})
            projects = await cursor.to_list(length=None)
            return projects
            
        except Exception as e:
            self.logger.error(f"Failed to get user projects: {str(e)}")
            raise
    
    async def delete_user(self, user_id: str):
        """Delete user account."""
        try:
            # Delete user
            result = await self.db.users.delete_one({"id": user_id})
            if result.deleted_count == 0:
                raise ResourceNotFoundError("User", user_id)
            
            # Delete user's projects
            await self.db.projects.delete_many({"user_id": user_id})
            
            # Delete user's backups
            await self.db.backups.delete_many({"user_id": user_id})
            
        except Exception as e:
            self.logger.error(f"User deletion failed: {str(e)}")
            raise 