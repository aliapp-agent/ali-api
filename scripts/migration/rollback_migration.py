#!/usr/bin/env python3
"""
Rollback script for Firebase migration.

This script provides rollback capabilities for Firebase migration,
allowing to revert changes if something goes wrong.
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import List, Dict, Any
import logging

# Add app to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.core.firebase import get_firestore, get_firebase_auth
from app.services.firebase_auth import firebase_auth_service

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FirebaseRollbackService:
    """Service to rollback Firebase migration."""
    
    def __init__(self):
        """Initialize rollback service."""
        self.firestore_db = get_firestore()
        self.firebase_auth = get_firebase_auth()
        
        self.rollback_stats = {
            'users_deleted': 0,
            'sessions_deleted': 0,
            'messages_deleted': 0,
            'documents_deleted': 0,
            'errors': 0
        }
    
    async def rollback_all(self) -> Dict[str, int]:
        """Rollback all migrated data.
        
        Returns:
            Dict[str, int]: Rollback statistics
        """
        logger.info("🔄 Starting rollback of Firebase migration")
        
        try:
            # Step 1: Delete messages
            logger.info("🗑️ Step 1: Deleting messages...")
            await self.rollback_messages()
            
            # Step 2: Delete sessions
            logger.info("🗑️ Step 2: Deleting sessions...")
            await self.rollback_sessions()
            
            # Step 3: Delete users from Firestore
            logger.info("🗑️ Step 3: Deleting user profiles...")
            await self.rollback_user_profiles()
            
            # Step 4: Delete users from Firebase Auth
            logger.info("🗑️ Step 4: Deleting Firebase Auth users...")
            await self.rollback_firebase_users()
            
            logger.info("✅ Rollback completed successfully!")
            self.print_rollback_stats()
            
        except Exception as e:
            logger.error(f"❌ Rollback failed: {e}")
            raise
        
        return self.rollback_stats
    
    async def rollback_messages(self) -> None:
        """Delete all migrated messages."""
        try:
            # Get all sessions
            sessions_ref = self.firestore_db.collection('chat_sessions')
            sessions = sessions_ref.where('migrated_from_pg', '==', True).stream()
            
            batch = self.firestore_db.batch()
            batch_count = 0
            
            for session in sessions:
                # Get all messages in this session
                messages_ref = session.reference.collection('messages')
                messages = messages_ref.where('migrated_from_pg', '==', True).stream()
                
                for message in messages:
                    batch.delete(message.reference)
                    batch_count += 1
                    self.rollback_stats['messages_deleted'] += 1
                    
                    # Commit batch every 500 operations
                    if batch_count >= 500:
                        batch.commit()
                        batch = self.firestore_db.batch()
                        batch_count = 0
                        logger.info(f"Deleted {self.rollback_stats['messages_deleted']} messages...")
            
            # Commit remaining operations
            if batch_count > 0:
                batch.commit()
                
            logger.info(f"✅ Deleted {self.rollback_stats['messages_deleted']} messages")
            
        except Exception as e:
            logger.error(f"❌ Failed to delete messages: {e}")
            self.rollback_stats['errors'] += 1
    
    async def rollback_sessions(self) -> None:
        """Delete all migrated sessions."""
        try:
            sessions_ref = self.firestore_db.collection('chat_sessions')
            sessions = sessions_ref.where('migrated_from_pg', '==', True).stream()
            
            batch = self.firestore_db.batch()
            batch_count = 0
            
            for session in sessions:
                batch.delete(session.reference)
                batch_count += 1
                self.rollback_stats['sessions_deleted'] += 1
                
                # Commit batch every 500 operations
                if batch_count >= 500:
                    batch.commit()
                    batch = self.firestore_db.batch()
                    batch_count = 0
                    logger.info(f"Deleted {self.rollback_stats['sessions_deleted']} sessions...")
            
            # Commit remaining operations
            if batch_count > 0:
                batch.commit()
                
            logger.info(f"✅ Deleted {self.rollback_stats['sessions_deleted']} sessions")
            
        except Exception as e:
            logger.error(f"❌ Failed to delete sessions: {e}")
            self.rollback_stats['errors'] += 1
    
    async def rollback_user_profiles(self) -> None:
        """Delete all migrated user profiles from Firestore."""
        try:
            users_ref = self.firestore_db.collection('users')
            users = users_ref.where('migrated_from_pg', '==', True).stream()
            
            batch = self.firestore_db.batch()
            batch_count = 0
            user_uids = []
            
            for user in users:
                batch.delete(user.reference)
                batch_count += 1
                user_uids.append(user.id)
                
                # Commit batch every 500 operations
                if batch_count >= 500:
                    batch.commit()
                    batch = self.firestore_db.batch()
                    batch_count = 0
                    logger.info(f"Deleted {len(user_uids)} user profiles...")
            
            # Commit remaining operations
            if batch_count > 0:
                batch.commit()
            
            self.rollback_stats['users_deleted'] = len(user_uids)
            logger.info(f"✅ Deleted {len(user_uids)} user profiles")
            
            # Store UIDs for Firebase Auth deletion
            self.migrated_user_uids = user_uids
            
        except Exception as e:
            logger.error(f"❌ Failed to delete user profiles: {e}")
            self.rollback_stats['errors'] += 1
    
    async def rollback_firebase_users(self) -> None:
        """Delete all migrated users from Firebase Auth."""
        try:
            if not hasattr(self, 'migrated_user_uids'):
                logger.warning("No user UIDs found for Firebase Auth deletion")
                return
            
            for uid in self.migrated_user_uids:
                try:
                    await firebase_auth_service.delete_user(uid)
                    logger.info(f"✅ Deleted Firebase Auth user: {uid}")
                except Exception as e:
                    logger.error(f"❌ Failed to delete Firebase Auth user {uid}: {e}")
                    self.rollback_stats['errors'] += 1
            
            logger.info(f"✅ Processed {len(self.migrated_user_uids)} Firebase Auth users")
            
        except Exception as e:
            logger.error(f"❌ Failed to delete Firebase Auth users: {e}")
            self.rollback_stats['errors'] += 1
    
    async def rollback_specific_user(self, user_email: str) -> bool:
        """Rollback specific user and their data.
        
        Args:
            user_email: User email to rollback
            
        Returns:
            bool: True if successful
        """
        try:
            logger.info(f"🔄 Rolling back user: {user_email}")
            
            # Find user in Firestore
            users_ref = self.firestore_db.collection('users')
            users_query = users_ref.where('email', '==', user_email).where('migrated_from_pg', '==', True)
            users = list(users_query.stream())
            
            if not users:
                logger.warning(f"User {user_email} not found in migrated data")
                return False
            
            user_doc = users[0]
            uid = user_doc.id
            
            # Delete user's sessions and messages
            sessions_ref = self.firestore_db.collection('chat_sessions')
            user_sessions = sessions_ref.where('user_id', '==', uid).stream()
            
            batch = self.firestore_db.batch()
            
            for session in user_sessions:
                # Delete messages
                messages_ref = session.reference.collection('messages')
                messages = messages_ref.stream()
                for message in messages:
                    batch.delete(message.reference)
                
                # Delete session
                batch.delete(session.reference)
            
            # Delete user profile
            batch.delete(user_doc.reference)
            
            # Commit batch
            batch.commit()
            
            # Delete from Firebase Auth
            await firebase_auth_service.delete_user(uid)
            
            logger.info(f"✅ Successfully rolled back user: {user_email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to rollback user {user_email}: {e}")
            return False
    
    def print_rollback_stats(self) -> None:
        """Print rollback statistics."""
        logger.info("\n" + "="*50)
        logger.info("📊 ROLLBACK STATISTICS")
        logger.info("="*50)
        logger.info(f"Users deleted: {self.rollback_stats['users_deleted']}")
        logger.info(f"Sessions deleted: {self.rollback_stats['sessions_deleted']}")
        logger.info(f"Messages deleted: {self.rollback_stats['messages_deleted']}")
        logger.info(f"Documents deleted: {self.rollback_stats['documents_deleted']}")
        logger.info(f"Errors: {self.rollback_stats['errors']}")
        logger.info("="*50)


async def main():
    """Main rollback function."""
    rollback_service = FirebaseRollbackService()
    
    print("🔄 Firebase Migration Rollback Tool")
    print("⚠️  WARNING: This will DELETE ALL migrated data from Firebase!")
    print("This includes:")
    print("- All users from Firebase Auth")
    print("- All user profiles from Firestore")
    print("- All chat sessions and messages")
    print("- All migrated documents")
    
    print("\nMake sure you have:")
    print("1. ✅ Backup of Firebase data (if needed)")
    print("2. ✅ PostgreSQL data is still intact")
    print("3. ✅ Understanding that this action cannot be undone")
    
    confirm = input("\nProceed with COMPLETE rollback? Type 'DELETE_ALL' to confirm: ")
    if confirm != 'DELETE_ALL':
        print("Rollback cancelled.")
        return
    
    final_confirm = input("Are you absolutely sure? (yes/no): ")
    if final_confirm.lower() != 'yes':
        print("Rollback cancelled.")
        return
    
    try:
        stats = await rollback_service.rollback_all()
        print(f"\n✅ Rollback completed! Check logs for details.")
        return stats
    except Exception as e:
        print(f"\n❌ Rollback failed: {e}")
        return None


async def rollback_user(email: str):
    """Rollback specific user."""
    rollback_service = FirebaseRollbackService()
    
    print(f"🔄 Rolling back user: {email}")
    confirm = input(f"Delete all data for {email}? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Rollback cancelled.")
        return
    
    success = await rollback_service.rollback_specific_user(email)
    if success:
        print(f"✅ User {email} rolled back successfully")
    else:
        print(f"❌ Failed to rollback user {email}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Firebase Migration Rollback')
    parser.add_argument('--user', help='Rollback specific user by email')
    args = parser.parse_args()
    
    if args.user:
        asyncio.run(rollback_user(args.user))
    else:
        asyncio.run(main())