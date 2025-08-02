"""Firebase Authentication service.

This module provides Firebase Authentication integration for user management,
token verification, and user profile management.
"""

from datetime import datetime
from typing import (
    Any,
    Dict,
    List,
    Optional,
)

from firebase_admin import auth
from firebase_admin.exceptions import FirebaseError

from app.core.firebase import get_firebase_auth
from app.shared.exceptions.auth import (
    AuthenticationError,
    AuthorizationError,
)


class FirebaseAuthService:
    """Firebase Authentication service."""

    def __init__(self):
        """Initialize Firebase Auth service."""
        self.auth = get_firebase_auth()

    async def create_user(
        self,
        email: str,
        password: str,
        display_name: Optional[str] = None,
        **additional_claims,
    ) -> str:
        """Create a new user in Firebase Auth.

        Args:
            email: User email address
            password: User password
            display_name: Optional display name
            **additional_claims: Additional user claims

        Returns:
            str: User UID

        Raises:
            AuthenticationError: If user creation fails
        """
        try:
            user_record = self.auth.create_user(
                email=email,
                password=password,
                display_name=display_name,
                email_verified=False,
            )

            # Set custom claims if provided
            if additional_claims:
                self.auth.set_custom_user_claims(user_record.uid, additional_claims)

            return user_record.uid

        except FirebaseError as e:
            raise AuthenticationError(f"Failed to create user: {e}")

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email address.

        Args:
            email: User email address

        Returns:
            Optional[Dict[str, Any]]: User data or None if not found
        """
        try:
            user_record = self.auth.get_user_by_email(email)
            return self._user_record_to_dict(user_record)
        except auth.UserNotFoundError:
            return None
        except FirebaseError as e:
            raise AuthenticationError(f"Failed to get user: {e}")

    async def get_user_by_uid(self, uid: str) -> Optional[Dict[str, Any]]:
        """Get user by UID.

        Args:
            uid: User UID

        Returns:
            Optional[Dict[str, Any]]: User data or None if not found
        """
        try:
            user_record = self.auth.get_user(uid)
            return self._user_record_to_dict(user_record)
        except auth.UserNotFoundError:
            return None
        except FirebaseError as e:
            raise AuthenticationError(f"Failed to get user: {e}")

    async def verify_token(self, id_token: str) -> Dict[str, Any]:
        """Verify Firebase ID token.

        Args:
            id_token: Firebase ID token

        Returns:
            Dict[str, Any]: Decoded token with user claims

        Raises:
            AuthenticationError: If token verification fails
        """
        try:
            decoded_token = self.auth.verify_id_token(id_token)
            return decoded_token
        except FirebaseError as e:
            raise AuthenticationError(f"Invalid token: {e}")

    async def update_user(
        self,
        uid: str,
        email: Optional[str] = None,
        display_name: Optional[str] = None,
        password: Optional[str] = None,
        email_verified: Optional[bool] = None,
        custom_claims: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Update user information.

        Args:
            uid: User UID
            email: New email address
            display_name: New display name
            password: New password
            email_verified: Email verification status
            custom_claims: Custom claims to set

        Returns:
            Dict[str, Any]: Updated user data

        Raises:
            AuthenticationError: If update fails
        """
        try:
            # Update basic user info
            update_kwargs = {}
            if email is not None:
                update_kwargs["email"] = email
            if display_name is not None:
                update_kwargs["display_name"] = display_name
            if password is not None:
                update_kwargs["password"] = password
            if email_verified is not None:
                update_kwargs["email_verified"] = email_verified

            if update_kwargs:
                user_record = self.auth.update_user(uid, **update_kwargs)
            else:
                user_record = self.auth.get_user(uid)

            # Update custom claims if provided
            if custom_claims is not None:
                self.auth.set_custom_user_claims(uid, custom_claims)

            return self._user_record_to_dict(user_record)

        except FirebaseError as e:
            raise AuthenticationError(f"Failed to update user: {e}")

    async def delete_user(self, uid: str) -> None:
        """Delete user from Firebase Auth.

        Args:
            uid: User UID

        Raises:
            AuthenticationError: If deletion fails
        """
        try:
            self.auth.delete_user(uid)
        except FirebaseError as e:
            raise AuthenticationError(f"Failed to delete user: {e}")

    async def list_users(
        self, page_token: Optional[str] = None, max_results: int = 1000
    ) -> Dict[str, Any]:
        """List all users.

        Args:
            page_token: Token for pagination
            max_results: Maximum number of results

        Returns:
            Dict[str, Any]: Users list with pagination info
        """
        try:
            page = self.auth.list_users(page_token=page_token, max_results=max_results)

            users = [self._user_record_to_dict(user) for user in page.users]

            return {
                "users": users,
                "next_page_token": page.next_page_token,
                "has_next_page": page.has_next_page,
            }

        except FirebaseError as e:
            raise AuthenticationError(f"Failed to list users: {e}")

    async def set_custom_claims(self, uid: str, claims: Dict[str, Any]) -> None:
        """Set custom claims for user.

        Args:
            uid: User UID
            claims: Custom claims to set

        Raises:
            AuthenticationError: If setting claims fails
        """
        try:
            self.auth.set_custom_user_claims(uid, claims)
        except FirebaseError as e:
            raise AuthenticationError(f"Failed to set custom claims: {e}")

    async def generate_password_reset_link(self, email: str) -> str:
        """Generate password reset link.

        Args:
            email: User email address

        Returns:
            str: Password reset link

        Raises:
            AuthenticationError: If link generation fails
        """
        try:
            link = self.auth.generate_password_reset_link(email)
            return link
        except FirebaseError as e:
            raise AuthenticationError(f"Failed to generate reset link: {e}")

    async def generate_email_verification_link(self, email: str) -> str:
        """Generate email verification link.

        Args:
            email: User email address

        Returns:
            str: Email verification link

        Raises:
            AuthenticationError: If link generation fails
        """
        try:
            link = self.auth.generate_email_verification_link(email)
            return link
        except FirebaseError as e:
            raise AuthenticationError(f"Failed to generate verification link: {e}")

    def _user_record_to_dict(self, user_record) -> Dict[str, Any]:
        """Convert Firebase UserRecord to dictionary.

        Args:
            user_record: Firebase UserRecord

        Returns:
            Dict[str, Any]: User data as dictionary
        """
        return {
            "uid": user_record.uid,
            "email": user_record.email,
            "email_verified": user_record.email_verified,
            "display_name": user_record.display_name,
            "photo_url": user_record.photo_url,
            "disabled": user_record.disabled,
            "metadata": (
                {
                    "creation_timestamp": user_record.user_metadata.creation_timestamp,
                    "last_sign_in_timestamp": user_record.user_metadata.last_sign_in_timestamp,
                }
                if user_record.user_metadata
                else None
            ),
            "custom_claims": user_record.custom_claims or {},
            "provider_data": [
                {
                    "uid": provider.uid,
                    "email": provider.email,
                    "display_name": provider.display_name,
                    "photo_url": provider.photo_url,
                    "provider_id": provider.provider_id,
                }
                for provider in user_record.provider_data
            ],
        }


# Global instance
firebase_auth_service = FirebaseAuthService()
