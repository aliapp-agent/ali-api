"""Firebase initialization and configuration.

This module handles Firebase Admin SDK initialization, service configuration,
and provides singleton instances for Firebase services.
"""

import os
from typing import Optional

import firebase_admin
from firebase_admin import (
    auth,
    credentials,
    firestore,
    storage,
)
from google.cloud import logging as cloud_logging
from google.cloud.storage import Bucket

from app.core.config import settings


class FirebaseConfig:
    """Firebase configuration and service manager."""

    def __init__(self):
        """Initialize Firebase configuration."""
        self._app: Optional[firebase_admin.App] = None
        self._firestore_client: Optional[firestore.Client] = None
        self._storage_client: Optional[Bucket] = None
        self._logging_client: Optional[cloud_logging.Client] = None
        self._auth_client = None

    def initialize(self) -> None:
        """Initialize Firebase Admin SDK."""
        if self._app is not None:
            return  # Already initialized

        try:
            # Initialize with service account credentials
            if (
                hasattr(settings, "FIREBASE_CREDENTIALS_PATH")
                and settings.FIREBASE_CREDENTIALS_PATH
                and os.path.exists(settings.FIREBASE_CREDENTIALS_PATH)
            ):
                cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
                self._app = firebase_admin.initialize_app(
                    cred,
                    {
                        "storageBucket": settings.FIREBASE_STORAGE_BUCKET,
                        "projectId": settings.FIREBASE_PROJECT_ID,
                    },
                )
            else:
                # Initialize with default credentials (for GCP environments)
                # This will use Application Default Credentials (ADC)
                self._app = firebase_admin.initialize_app(
                    options={
                        "storageBucket": settings.FIREBASE_STORAGE_BUCKET,
                        "projectId": settings.FIREBASE_PROJECT_ID,
                    }
                )

        except Exception as e:
            raise RuntimeError(f"Failed to initialize Firebase: {e}")

    @property
    def firestore(self) -> firestore.Client:
        """Get Firestore client."""
        if self._firestore_client is None:
            self.initialize()
            self._firestore_client = firestore.client(app=self._app)
        return self._firestore_client

    @property
    def storage(self) -> Bucket:
        """Get Cloud Storage bucket."""
        if self._storage_client is None:
            self.initialize()
            self._storage_client = storage.bucket(app=self._app)
        return self._storage_client

    @property
    def auth(self):
        """Get Firebase Auth client."""
        if self._auth_client is None:
            self.initialize()
            self._auth_client = auth
        return self._auth_client

    @property
    def logging(self) -> cloud_logging.Client:
        """Get Cloud Logging client."""
        if self._logging_client is None:
            self._logging_client = cloud_logging.Client()
        return self._logging_client


# Global Firebase instance
firebase_config = FirebaseConfig()


def get_firestore() -> firestore.Client:
    """Get Firestore client instance."""
    return firebase_config.firestore


def get_storage():
    """Get Cloud Storage client instance."""
    return firebase_config.storage


def get_firebase_auth():
    """Get Firebase Auth client instance."""
    return firebase_config.auth


def get_cloud_logging() -> cloud_logging.Client:
    """Get Cloud Logging client instance."""
    return firebase_config.logging
