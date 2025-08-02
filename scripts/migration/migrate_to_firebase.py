#!/usr/bin/env python3
"""Migration script from PostgreSQL to Firebase.

This script migrates data from PostgreSQL database to Firebase services:
- Users → Firebase Auth + Firestore
- Sessions → Firestore
- Messages → Firestore subcollections
- Documents → Firestore + Cloud Storage
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import (
    Any,
    Dict,
    List,
    Optional,
)

# Add app to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from sqlalchemy import (
    create_engine,
    text,
)
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.firebase import (
    get_firebase_auth,
    get_firestore,
    get_storage,
)
from app.infrastructure.firestore.session_repository import FirestoreSessionRepository
from app.infrastructure.firestore.user_repository import FirestoreUserRepository
from app.services.firebase_auth import firebase_auth_service

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class FirebaseMigrationService:
    """Service to handle migration from PostgreSQL to Firebase."""

    def __init__(self):
        """Initialize migration service."""
        self.pg_engine = create_engine(settings.POSTGRES_URL)
        self.pg_session = sessionmaker(bind=self.pg_engine)()

        self.firestore_db = get_firestore()
        self.firebase_auth = get_firebase_auth()
        self.storage_bucket = get_storage()

        self.user_repo = FirestoreUserRepository()
        self.session_repo = FirestoreSessionRepository()

        self.migration_stats = {
            "users_migrated": 0,
            "users_failed": 0,
            "sessions_migrated": 0,
            "sessions_failed": 0,
            "messages_migrated": 0,
            "messages_failed": 0,
            "documents_migrated": 0,
            "documents_failed": 0,
        }

    async def migrate_all(self) -> Dict[str, int]:
        """Migrate all data from PostgreSQL to Firebase.

        Returns:
            Dict[str, int]: Migration statistics
        """
        logger.info("🚀 Starting migration from PostgreSQL to Firebase")

        try:
            # Step 1: Migrate users
            logger.info("📝 Step 1: Migrating users...")
            await self.migrate_users()

            # Step 2: Migrate sessions
            logger.info("💬 Step 2: Migrating chat sessions...")
            await self.migrate_sessions()

            # Step 3: Migrate messages
            logger.info("📨 Step 3: Migrating messages...")
            await self.migrate_messages()

            # Step 4: Migrate documents (if exists)
            logger.info("📄 Step 4: Migrating documents...")
            await self.migrate_documents()

            logger.info("✅ Migration completed successfully!")
            self.print_migration_stats()

        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            raise

        finally:
            self.pg_session.close()

        return self.migration_stats

    async def migrate_users(self) -> None:
        """Migrate users from PostgreSQL to Firebase Auth + Firestore."""
        logger.info("Fetching users from PostgreSQL...")

        # Fetch all users from PostgreSQL
        query = text(
            """
            SELECT id, email, hashed_password, role, status, permissions, 
                   preferences, profile, is_verified, is_active, last_login, 
                   login_count, created_at, updated_at
            FROM "user"
            ORDER BY created_at
        """
        )

        result = self.pg_session.execute(query)
        users = result.fetchall()

        logger.info(f"Found {len(users)} users to migrate")

        for user_row in users:
            try:
                # Create user in Firebase Auth
                firebase_user = await self.create_firebase_user(user_row)

                # Create user profile in Firestore
                await self.create_firestore_user(user_row, firebase_user["uid"])

                self.migration_stats["users_migrated"] += 1
                logger.info(f"✅ Migrated user: {user_row.email}")

            except Exception as e:
                self.migration_stats["users_failed"] += 1
                logger.error(f"❌ Failed to migrate user {user_row.email}: {e}")

    async def create_firebase_user(self, user_row) -> Dict[str, Any]:
        """Create user in Firebase Auth.

        Args:
            user_row: PostgreSQL user row

        Returns:
            Dict[str, Any]: Created Firebase user data
        """
        # Generate a temporary password (user will need to reset)
        temp_password = f"temp_{user_row.id}_{int(datetime.now().timestamp())}"

        # Custom claims for roles and permissions
        custom_claims = {
            "role": user_row.role or "viewer",
            "permissions": user_row.permissions or {},
            "migrated_from_pg": True,
            "original_id": str(user_row.id),
        }

        firebase_user = await firebase_auth_service.create_user(
            email=user_row.email,
            password=temp_password,
            display_name=self.extract_display_name(user_row),
            **custom_claims,
        )

        return {"uid": firebase_user}

    async def create_firestore_user(self, user_row, firebase_uid: str) -> None:
        """Create user profile in Firestore.

        Args:
            user_row: PostgreSQL user row
            firebase_uid: Firebase user UID
        """
        user_data = {
            "id": firebase_uid,
            "email": user_row.email,
            "role": user_row.role or "viewer",
            "status": user_row.status or "active",
            "permissions": user_row.permissions,
            "preferences": user_row.preferences,
            "profile": user_row.profile,
            "is_verified": user_row.is_verified or False,
            "is_active": user_row.is_active if user_row.is_active is not None else True,
            "last_login": user_row.last_login,
            "login_count": user_row.login_count or 0,
            "created_at": user_row.created_at,
            "updated_at": user_row.updated_at,
            "migrated_from_pg": True,
            "original_pg_id": user_row.id,
        }

        await self.user_repo.create(user_data, firebase_uid)

    async def migrate_sessions(self) -> None:
        """Migrate chat sessions from PostgreSQL to Firestore."""
        logger.info("Fetching sessions from PostgreSQL...")

        query = text(
            """
            SELECT s.id, s.user_id, s.name, s.created_at,
                   u.email as user_email
            FROM session s
            JOIN "user" u ON s.user_id = u.id
            ORDER BY s.created_at
        """
        )

        result = self.pg_session.execute(query)
        sessions = result.fetchall()

        logger.info(f"Found {len(sessions)} sessions to migrate")

        # Get user mapping (PG ID → Firebase UID)
        user_mapping = await self.get_user_mapping()

        for session_row in sessions:
            try:
                # Get Firebase UID for user
                firebase_uid = user_mapping.get(session_row.user_id)
                if not firebase_uid:
                    logger.warning(
                        f"User {session_row.user_id} not found in Firebase, skipping session {session_row.id}"
                    )
                    continue

                session_data = {
                    "user_id": firebase_uid,
                    "name": session_row.name or f"Chat {session_row.id}",
                    "session_type": "chat",
                    "status": "active",
                    "message_count": 0,
                    "total_tokens": 0,
                    "total_response_time": 0.0,
                    "created_at": session_row.created_at,
                    "updated_at": session_row.created_at,
                    "migrated_from_pg": True,
                    "original_pg_id": session_row.id,
                }

                await self.session_repo.create(session_data, session_row.id)

                self.migration_stats["sessions_migrated"] += 1
                logger.info(f"✅ Migrated session: {session_row.id}")

            except Exception as e:
                self.migration_stats["sessions_failed"] += 1
                logger.error(f"❌ Failed to migrate session {session_row.id}: {e}")

    async def migrate_messages(self) -> None:
        """Migrate messages to Firestore subcollections."""
        logger.info("Checking for messages table...")

        # Check if messages table exists
        try:
            query = text(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'message' OR table_name = 'chat_message'
                )
            """
            )
            exists = self.pg_session.execute(query).scalar()

            if not exists:
                logger.info("No messages table found, skipping message migration")
                return

            # Try different possible table names
            for table_name in ["chat_message", "message"]:
                try:
                    query = text(
                        f"""
                        SELECT m.id, m.session_id, m.role, m.content, m.created_at
                        FROM {table_name} m
                        ORDER BY m.created_at
                        LIMIT 10
                    """
                    )
                    result = self.pg_session.execute(query)
                    messages = result.fetchall()

                    if messages:
                        logger.info(
                            f"Found {len(messages)} messages in {table_name} to migrate"
                        )
                        await self.migrate_messages_from_table(table_name)
                        break

                except Exception:
                    continue

        except Exception as e:
            logger.info(f"Messages migration skipped: {e}")

    async def migrate_messages_from_table(self, table_name: str) -> None:
        """Migrate messages from specific table.

        Args:
            table_name: Name of the messages table
        """
        query = text(
            f"""
            SELECT m.id, m.session_id, m.role, m.content, m.created_at,
                   s.id as session_exists
            FROM {table_name} m
            LEFT JOIN session s ON m.session_id = s.id
            ORDER BY m.created_at
        """
        )

        result = self.pg_session.execute(query)
        messages = result.fetchall()

        for message_row in messages:
            try:
                if not message_row.session_exists:
                    logger.warning(
                        f"Session {message_row.session_id} not found, skipping message {message_row.id}"
                    )
                    continue

                # Add message to session subcollection
                session_ref = self.firestore_db.collection("chat_sessions").document(
                    str(message_row.session_id)
                )
                messages_ref = session_ref.collection("messages")

                message_data = {
                    "role": message_row.role,
                    "content": message_row.content,
                    "timestamp": message_row.created_at,
                    "migrated_from_pg": True,
                    "original_pg_id": message_row.id,
                }

                messages_ref.document(str(message_row.id)).set(message_data)

                self.migration_stats["messages_migrated"] += 1

                if self.migration_stats["messages_migrated"] % 100 == 0:
                    logger.info(
                        f"✅ Migrated {self.migration_stats['messages_migrated']} messages..."
                    )

            except Exception as e:
                self.migration_stats["messages_failed"] += 1
                logger.error(f"❌ Failed to migrate message {message_row.id}: {e}")

    async def migrate_documents(self) -> None:
        """Migrate documents if they exist."""
        logger.info("Checking for documents...")

        try:
            # Check if documents table exists
            query = text(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'document' OR table_name = 'documents'
                )
            """
            )
            exists = self.pg_session.execute(query).scalar()

            if not exists:
                logger.info("No documents table found, skipping document migration")
                return

            # Implementation for document migration would go here
            logger.info(
                "Document migration not implemented yet - manual migration required"
            )

        except Exception as e:
            logger.info(f"Documents migration skipped: {e}")

    async def get_user_mapping(self) -> Dict[int, str]:
        """Get mapping from PostgreSQL user ID to Firebase UID.

        Returns:
            Dict[int, str]: Mapping of PG user ID to Firebase UID
        """
        mapping = {}

        # Get all users from Firestore with original PG IDs
        users_ref = self.firestore_db.collection("users")
        docs = users_ref.where("migrated_from_pg", "==", True).stream()

        for doc in docs:
            data = doc.to_dict()
            if "original_pg_id" in data:
                mapping[data["original_pg_id"]] = doc.id

        return mapping

    def extract_display_name(self, user_row) -> Optional[str]:
        """Extract display name from user profile.

        Args:
            user_row: PostgreSQL user row

        Returns:
            Optional[str]: Display name or None
        """
        if user_row.profile and isinstance(user_row.profile, dict):
            first_name = user_row.profile.get("first_name", "")
            last_name = user_row.profile.get("last_name", "")
            if first_name or last_name:
                return f"{first_name} {last_name}".strip()

        return user_row.email.split("@")[0] if user_row.email else None

    def print_migration_stats(self) -> None:
        """Print migration statistics."""
        logger.info("\n" + "=" * 50)
        logger.info("📊 MIGRATION STATISTICS")
        logger.info("=" * 50)
        logger.info(
            f"Users: {self.migration_stats['users_migrated']} migrated, {self.migration_stats['users_failed']} failed"
        )
        logger.info(
            f"Sessions: {self.migration_stats['sessions_migrated']} migrated, {self.migration_stats['sessions_failed']} failed"
        )
        logger.info(
            f"Messages: {self.migration_stats['messages_migrated']} migrated, {self.migration_stats['messages_failed']} failed"
        )
        logger.info(
            f"Documents: {self.migration_stats['documents_migrated']} migrated, {self.migration_stats['documents_failed']} failed"
        )
        logger.info("=" * 50)


async def main():
    """Main migration function."""
    migration_service = FirebaseMigrationService()

    # Ask for confirmation
    print("🔥 Firebase Migration Tool")
    print("This will migrate all data from PostgreSQL to Firebase.")
    print("Make sure you have:")
    print("1. ✅ Firebase project configured")
    print("2. ✅ Firebase credentials file in place")
    print("3. ✅ PostgreSQL database accessible")
    print("4. ✅ Backup of PostgreSQL data")

    confirm = input("\nProceed with migration? (yes/no): ")
    if confirm.lower() != "yes":
        print("Migration cancelled.")
        return

    try:
        stats = await migration_service.migrate_all()
        print("\n✅ Migration completed! Check logs for details.")
        return stats
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        return None


if __name__ == "__main__":
    asyncio.run(main())
