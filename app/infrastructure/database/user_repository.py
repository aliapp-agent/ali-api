"""PostgreSQL implementation of UserRepositoryInterface for Ali API.

This module contains the concrete implementation of user data access
using PostgreSQL and SQLModel.
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import and_, or_, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlmodel import Session, select, func

from app.core.config import settings
from app.core.logging import logger
from app.models.user import User as UserModel
from app.domain.entities import UserEntity, UserRole, UserStatus, UserProfile, UserPreferences
from app.domain.repositories import UserRepositoryInterface
from app.domain.exceptions import (
    UserAlreadyExistsError,
    UserNotFoundError,
    RepositoryError,
)


class PostgresUserRepository(UserRepositoryInterface):
    """PostgreSQL implementation of the user repository.
    
    This class implements user data access using PostgreSQL database
    through SQLModel ORM.
    """
    
    def __init__(self, db_session: Session):
        """Initialize the repository with a database session.
        
        Args:
            db_session: SQLModel database session
        """
        self.db_session = db_session

    async def create(self, user: UserEntity) -> UserEntity:
        """Create a new user in the database.
        
        Args:
            user: User entity to create
            
        Returns:
            UserEntity: Created user with assigned ID
            
        Raises:
            UserAlreadyExistsError: If user with email already exists
            RepositoryError: If creation fails
        """
        try:
            # Check if user already exists
            existing = self.db_session.exec(
                select(UserModel).where(UserModel.email == user.email)
            ).first()
            
            if existing:
                raise UserAlreadyExistsError(user.email)
            
            # Convert entity to model
            user_model = self._entity_to_model(user)
            
            # Save to database
            self.db_session.add(user_model)
            self.db_session.commit()
            self.db_session.refresh(user_model)
            
            logger.info(
                "user_created",
                user_id=user_model.id,
                email=user.email,
                role=user.role.value
            )
            
            # Convert back to entity
            return self._model_to_entity(user_model)
            
        except IntegrityError as e:
            self.db_session.rollback()
            if "email" in str(e).lower():
                raise UserAlreadyExistsError(user.email)
            else:
                raise RepositoryError(f"Failed to create user: {str(e)}")
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error("user_creation_failed", error=str(e), email=user.email)
            raise RepositoryError(f"Database error during user creation: {str(e)}")

    async def get_by_id(self, user_id: int) -> Optional[UserEntity]:
        """Get user by ID from the database.
        
        Args:
            user_id: User ID to lookup
            
        Returns:
            UserEntity or None if not found
        """
        try:
            user_model = self.db_session.get(UserModel, user_id)
            
            if not user_model:
                return None
            
            return self._model_to_entity(user_model)
            
        except SQLAlchemyError as e:
            logger.error("get_user_by_id_failed", error=str(e), user_id=user_id)
            raise RepositoryError(f"Database error during user lookup: {str(e)}")

    async def get_by_email(self, email: str) -> Optional[UserEntity]:
        """Get user by email address from the database.
        
        Args:
            email: Email address to lookup
            
        Returns:
            UserEntity or None if not found
        """
        try:
            user_model = self.db_session.exec(
                select(UserModel).where(UserModel.email == email.lower())
            ).first()
            
            if not user_model:
                return None
            
            return self._model_to_entity(user_model)
            
        except SQLAlchemyError as e:
            logger.error("get_user_by_email_failed", error=str(e), email=email)
            raise RepositoryError(f"Database error during user lookup: {str(e)}")

    async def update(self, user: UserEntity) -> UserEntity:
        """Update an existing user in the database.
        
        Args:
            user: User entity with updated data
            
        Returns:
            UserEntity: Updated user
            
        Raises:
            UserNotFoundError: If user doesn't exist
            RepositoryError: If update fails
        """
        try:
            # Get existing user
            user_model = self.db_session.get(UserModel, user.id)
            if not user_model:
                raise UserNotFoundError(user.id)
            
            # Update model fields
            self._update_model_from_entity(user_model, user)
            
            # Save changes
            self.db_session.commit()
            self.db_session.refresh(user_model)
            
            logger.info("user_updated", user_id=user.id, email=user.email)
            
            return self._model_to_entity(user_model)
            
        except UserNotFoundError:
            raise
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error("user_update_failed", error=str(e), user_id=user.id)
            raise RepositoryError(f"Database error during user update: {str(e)}")

    async def delete(self, user_id: int) -> bool:
        """Delete a user (soft delete) from the database.
        
        Args:
            user_id: ID of user to delete
            
        Returns:
            bool: True if deleted successfully
            
        Raises:
            UserNotFoundError: If user doesn't exist
        """
        try:
            user_model = self.db_session.get(UserModel, user_id)
            if not user_model:
                raise UserNotFoundError(user_id)
            
            # Soft delete by setting status
            user_model.status = UserStatus.DELETED.value
            user_model.is_active = False
            user_model.updated_at = datetime.utcnow()
            
            self.db_session.commit()
            
            logger.info("user_deleted", user_id=user_id)
            
            return True
            
        except UserNotFoundError:
            raise
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error("user_deletion_failed", error=str(e), user_id=user_id)
            raise RepositoryError(f"Database error during user deletion: {str(e)}")

    async def list_users(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[UserStatus] = None,
        role: Optional[UserRole] = None,
        is_verified: Optional[bool] = None,
        search_query: Optional[str] = None,
    ) -> List[UserEntity]:
        """List users with optional filtering.
        
        Args:
            limit: Maximum number of users to return
            offset: Number of users to skip
            status: Filter by user status
            role: Filter by user role
            is_verified: Filter by verification status
            search_query: Search in email or name
            
        Returns:
            List[UserEntity]: List of users matching criteria
        """
        try:
            query = select(UserModel)
            
            # Apply filters
            filters = []
            
            if status:
                filters.append(UserModel.status == status.value)
            
            if role:
                filters.append(UserModel.role == role.value)
            
            if is_verified is not None:
                filters.append(UserModel.is_verified == is_verified)
            
            if search_query:
                search_term = f"%{search_query.lower()}%"
                filters.append(
                    or_(
                        UserModel.email.ilike(search_term),
                        UserModel.profile["first_name"].astext.ilike(search_term),
                        UserModel.profile["last_name"].astext.ilike(search_term)
                    )
                )
            
            if filters:
                query = query.where(and_(*filters))
            
            # Apply pagination and ordering
            query = query.offset(offset).limit(limit).order_by(UserModel.created_at.desc())
            
            user_models = self.db_session.exec(query).all()
            
            return [self._model_to_entity(model) for model in user_models]
            
        except SQLAlchemyError as e:
            logger.error("list_users_failed", error=str(e))
            raise RepositoryError(f"Database error during user listing: {str(e)}")

    async def count_users(
        self,
        status: Optional[UserStatus] = None,
        role: Optional[UserRole] = None,
        is_verified: Optional[bool] = None,
        search_query: Optional[str] = None,
    ) -> int:
        """Count users with optional filtering.
        
        Args:
            status: Filter by user status
            role: Filter by user role
            is_verified: Filter by verification status
            search_query: Search in email or name
            
        Returns:
            int: Number of users matching criteria
        """
        try:
            query = select(func.count(UserModel.id))
            
            # Apply same filters as list_users
            filters = []
            
            if status:
                filters.append(UserModel.status == status.value)
            
            if role:
                filters.append(UserModel.role == role.value)
            
            if is_verified is not None:
                filters.append(UserModel.is_verified == is_verified)
            
            if search_query:
                search_term = f"%{search_query.lower()}%"
                filters.append(
                    or_(
                        UserModel.email.ilike(search_term),
                        UserModel.profile["first_name"].astext.ilike(search_term),
                        UserModel.profile["last_name"].astext.ilike(search_term)
                    )
                )
            
            if filters:
                query = query.where(and_(*filters))
            
            count = self.db_session.exec(query).one()
            return count
            
        except SQLAlchemyError as e:
            logger.error("count_users_failed", error=str(e))
            raise RepositoryError(f"Database error during user counting: {str(e)}")

    async def exists_by_email(self, email: str) -> bool:
        """Check if user exists by email.
        
        Args:
            email: Email address to check
            
        Returns:
            bool: True if user exists
        """
        try:
            count = self.db_session.exec(
                select(func.count(UserModel.id)).where(UserModel.email == email.lower())
            ).one()
            
            return count > 0
            
        except SQLAlchemyError as e:
            logger.error("exists_by_email_failed", error=str(e), email=email)
            raise RepositoryError(f"Database error during email check: {str(e)}")

    async def get_active_users(self, limit: int = 100) -> List[UserEntity]:
        """Get active users.
        
        Args:
            limit: Maximum number of users to return
            
        Returns:
            List[UserEntity]: List of active users
        """
        return await self.list_users(
            limit=limit,
            status=UserStatus.ACTIVE,
            is_verified=True
        )

    async def get_users_by_role(self, role: UserRole) -> List[UserEntity]:
        """Get users by role.
        
        Args:
            role: User role to filter by
            
        Returns:
            List[UserEntity]: List of users with specified role
        """
        return await self.list_users(role=role, limit=1000)

    async def get_unverified_users(
        self, 
        created_before: datetime,
        limit: int = 100
    ) -> List[UserEntity]:
        """Get unverified users created before a certain date.
        
        Args:
            created_before: Cutoff date for user creation
            limit: Maximum number of users to return
            
        Returns:
            List[UserEntity]: List of unverified users
        """
        try:
            query = select(UserModel).where(
                and_(
                    UserModel.is_verified == False,
                    UserModel.created_at < created_before,
                    UserModel.status != UserStatus.DELETED.value
                )
            ).limit(limit).order_by(UserModel.created_at.asc())
            
            user_models = self.db_session.exec(query).all()
            
            return [self._model_to_entity(model) for model in user_models]
            
        except SQLAlchemyError as e:
            logger.error("get_unverified_users_failed", error=str(e))
            raise RepositoryError(f"Database error: {str(e)}")

    async def update_last_login(self, user_id: int) -> bool:
        """Update user's last login timestamp.
        
        Args:
            user_id: ID of user to update
            
        Returns:
            bool: True if updated successfully
        """
        try:
            user_model = self.db_session.get(UserModel, user_id)
            if not user_model:
                return False
            
            user_model.last_login = datetime.utcnow()
            user_model.login_count += 1
            user_model.updated_at = datetime.utcnow()
            
            self.db_session.commit()
            return True
            
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error("update_last_login_failed", error=str(e), user_id=user_id)
            return False

    async def increment_login_count(self, user_id: int) -> bool:
        """Increment user's login count.
        
        Args:
            user_id: ID of user to update
            
        Returns:
            bool: True if updated successfully
        """
        return await self.update_last_login(user_id)  # Already increments login count

    async def bulk_update_status(
        self, 
        user_ids: List[int], 
        status: UserStatus
    ) -> int:
        """Bulk update user status.
        
        Args:
            user_ids: List of user IDs to update
            status: New status to set
            
        Returns:
            int: Number of users updated
        """
        try:
            if not user_ids:
                return 0
            
            # Use raw SQL for bulk update
            result = self.db_session.exec(
                text("""
                    UPDATE users 
                    SET status = :status, updated_at = :updated_at 
                    WHERE id = ANY(:user_ids)
                """),
                {
                    "status": status.value,
                    "updated_at": datetime.utcnow(),
                    "user_ids": user_ids
                }
            )
            
            self.db_session.commit()
            
            affected_rows = result.rowcount
            logger.info("bulk_status_update", count=affected_rows, status=status.value)
            
            return affected_rows
            
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error("bulk_update_status_failed", error=str(e))
            raise RepositoryError(f"Database error during bulk update: {str(e)}")

    async def get_user_statistics(self) -> dict:
        """Get user statistics.
        
        Returns:
            dict: Statistics including total users, by status, by role, etc.
        """
        try:
            # Total users
            total_users = self.db_session.exec(
                select(func.count(UserModel.id))
            ).one()
            
            # Users by status
            status_stats = {}
            for status in UserStatus:
                count = self.db_session.exec(
                    select(func.count(UserModel.id)).where(UserModel.status == status.value)
                ).one()
                status_stats[status.value] = count
            
            # Users by role
            role_stats = {}
            for role in UserRole:
                count = self.db_session.exec(
                    select(func.count(UserModel.id)).where(UserModel.role == role.value)
                ).one()
                role_stats[role.value] = count
            
            # Verified users
            verified_count = self.db_session.exec(
                select(func.count(UserModel.id)).where(UserModel.is_verified == True)
            ).one()
            
            return {
                "total_users": total_users,
                "verified_users": verified_count,
                "unverified_users": total_users - verified_count,
                "by_status": status_stats,
                "by_role": role_stats,
                "verification_rate": round(verified_count / total_users * 100, 2) if total_users > 0 else 0
            }
            
        except SQLAlchemyError as e:
            logger.error("get_user_statistics_failed", error=str(e))
            raise RepositoryError(f"Database error during statistics: {str(e)}")

    async def search_users(
        self,
        query: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[UserEntity]:
        """Search users by various fields.
        
        Args:
            query: Search query (email, name, etc.)
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List[UserEntity]: List of users matching search
        """
        return await self.list_users(
            limit=limit,
            offset=offset,
            search_query=query
        )

    def _entity_to_model(self, entity: UserEntity) -> UserModel:
        """Convert UserEntity to UserModel.
        
        Args:
            entity: User entity to convert
            
        Returns:
            UserModel: Converted user model
        """
        # Convert profile and preferences to dict
        profile_dict = {
            "first_name": entity.profile.first_name,
            "last_name": entity.profile.last_name,
            "avatar_url": entity.profile.avatar_url,
            "bio": entity.profile.bio,
            "phone": entity.profile.phone,
            "timezone": entity.profile.timezone,
            "language": entity.profile.language,
        }
        
        preferences_dict = {
            "theme": entity.preferences.theme,
            "notifications_enabled": entity.preferences.notifications_enabled,
            "email_notifications": entity.preferences.email_notifications,
            "auto_save": entity.preferences.auto_save,
            "default_language": entity.preferences.default_language,
        }
        
        return UserModel(
            id=entity.id,
            email=entity.email,
            hashed_password=entity.hashed_password,
            role=entity.role.value,
            status=entity.status.value,
            permissions=entity.permissions,
            preferences=preferences_dict,
            profile=profile_dict,
            is_verified=entity.is_verified,
            is_active=entity.is_active,
            last_login=entity.last_login,
            login_count=entity.login_count,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def _model_to_entity(self, model: UserModel) -> UserEntity:
        """Convert UserModel to UserEntity.
        
        Args:
            model: User model to convert
            
        Returns:
            UserEntity: Converted user entity
        """
        # Convert profile dict to UserProfile
        profile_data = model.profile or {}
        profile = UserProfile(
            first_name=profile_data.get("first_name"),
            last_name=profile_data.get("last_name"),
            avatar_url=profile_data.get("avatar_url"),
            bio=profile_data.get("bio"),
            phone=profile_data.get("phone"),
            timezone=profile_data.get("timezone"),
            language=profile_data.get("language", "pt-BR"),
        )
        
        # Convert preferences dict to UserPreferences
        preferences_data = model.preferences or {}
        preferences = UserPreferences(
            theme=preferences_data.get("theme", "light"),
            notifications_enabled=preferences_data.get("notifications_enabled", True),
            email_notifications=preferences_data.get("email_notifications", True),
            auto_save=preferences_data.get("auto_save", True),
            default_language=preferences_data.get("default_language", "pt-BR"),
        )
        
        return UserEntity(
            email=model.email,
            hashed_password=model.hashed_password,
            role=UserRole(model.role),
            status=UserStatus(model.status),
            permissions=model.permissions or [],
            preferences=preferences,
            profile=profile,
            is_verified=model.is_verified,
            is_active=model.is_active,
            last_login=model.last_login,
            login_count=model.login_count,
            created_at=model.created_at,
            updated_at=model.updated_at,
            user_id=model.id,
        )

    def _update_model_from_entity(self, model: UserModel, entity: UserEntity) -> None:
        """Update UserModel fields from UserEntity.
        
        Args:
            model: User model to update
            entity: User entity with new data
        """
        model.email = entity.email
        model.hashed_password = entity.hashed_password
        model.role = entity.role.value
        model.status = entity.status.value
        model.permissions = entity.permissions
        model.is_verified = entity.is_verified
        model.is_active = entity.is_active
        model.last_login = entity.last_login
        model.login_count = entity.login_count
        model.updated_at = entity.updated_at
        
        # Update profile
        model.profile = {
            "first_name": entity.profile.first_name,
            "last_name": entity.profile.last_name,
            "avatar_url": entity.profile.avatar_url,
            "bio": entity.profile.bio,
            "phone": entity.profile.phone,
            "timezone": entity.profile.timezone,
            "language": entity.profile.language,
        }
        
        # Update preferences
        model.preferences = {
            "theme": entity.preferences.theme,
            "notifications_enabled": entity.preferences.notifications_enabled,
            "email_notifications": entity.preferences.email_notifications,
            "auto_save": entity.preferences.auto_save,
            "default_language": entity.preferences.default_language,
        }