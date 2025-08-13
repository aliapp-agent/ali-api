"""Application configuration management.

This module handles environment-specific configuration loading, parsing, and management
for the application. It includes environment detection, .env file loading, and
configuration value parsing.
"""

import os
from enum import Enum
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings


# Define environment types
class Environment(str, Enum):
    """Application environment types.

    Defines the possible environments the application can run in:
    development, staging, production, and test.
    """

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"


# Determine environment
def get_environment() -> Environment:
    """Get the current environment.

    Returns:
        Environment: The current environment (development, staging, production, or test)
    """
    match os.getenv("APP_ENV", "development").lower():
        case "production" | "prod":
            return Environment.PRODUCTION
        case "staging" | "stage":
            return Environment.STAGING
        case "test":
            return Environment.TEST
        case _:
            return Environment.DEVELOPMENT


# Load .env file
def load_env_file():
    """Load .env file."""
    # Load main .env file
    if Path(".env").exists():
        load_dotenv(".env")
    
    # Also try to load .env.firebase if it exists (for Firebase-specific configs)
    firebase_env = ".env.firebase"
    if Path(firebase_env).exists():
        load_dotenv(firebase_env)


# Load environment file
load_env_file()


class Settings(BaseSettings):
    """Application settings.

    This class defines all configuration settings for the application,
    including database connections, API keys, and feature flags.
    """

    # Application Settings
    APP_ENV: Environment = Field(default=Environment.DEVELOPMENT, env="APP_ENV")
    PROJECT_NAME: str = Field(default="Ali API", env="PROJECT_NAME")
    VERSION: str = Field(default="1.0.0", env="VERSION")
    DESCRIPTION: str = Field(
        default="A production-ready FastAPI template with Agno and Langfuse integration",
        env="DESCRIPTION",
    )
    API_V1_STR: str = Field(default="/api/v1", env="API_V1_STR")
    APP_BASE_URL: str = Field(default="", env="APP_BASE_URL")
    DEBUG: bool = Field(default=False, env="DEBUG")

    # Firebase is now the primary database - PostgreSQL removed

    # Agno Memory Configuration
    AGNO_MEMORY_PATH: str = Field(
        default="./data/agno_memory.db", env="AGNO_MEMORY_PATH"
    )

    # Elasticsearch Configuration
    ELASTICSEARCH_URL: str = Field(
        default="http://localhost:9200", env="ELASTICSEARCH_URL"
    )
    ELASTICSEARCH_TIMEOUT: int = Field(default=30, env="ELASTICSEARCH_TIMEOUT")
    ELASTICSEARCH_MAX_RETRIES: int = Field(default=3, env="ELASTICSEARCH_MAX_RETRIES")
    ELASTICSEARCH_INDEX_NAME: str = Field(
        default="agua-clara-ms", env="ELASTICSEARCH_INDEX_NAME"
    )
    ELASTICSEARCH_API_KEY: str = Field(default="", env="ELASTICSEARCH_API_KEY")

    # RAG Configuration
    RAG_INDEX_NAME: str = Field(default="agua-clara-ms", env="RAG_INDEX_NAME")
    RAG_EMBEDDING_MODEL: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        env="RAG_EMBEDDING_MODEL",
    )
    RAG_CHUNK_SIZE: int = Field(default=1000, env="RAG_CHUNK_SIZE")
    RAG_CHUNK_OVERLAP: int = Field(default=200, env="RAG_CHUNK_OVERLAP")
    RAG_MAX_RESULTS: int = Field(default=5, env="RAG_MAX_RESULTS")

    # CORS Settings
    ALLOWED_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:8080,http://127.0.0.1:3000",
        env="ALLOWED_ORIGINS",
    )

    @property
    def ALLOWED_ORIGINS_LIST(self) -> list[str]:
        """Parse ALLOWED_ORIGINS string into a list."""
        origins = []
        
        # Check for individual origin environment variables (used in Cloud Run)
        allowed_origin_1 = os.getenv("ALLOWED_ORIGIN_1")
        allowed_origin_2 = os.getenv("ALLOWED_ORIGIN_2")
        
        if allowed_origin_1:
            origins.append(allowed_origin_1.strip())
        if allowed_origin_2:
            origins.append(allowed_origin_2.strip())
            
        # Fallback to comma-separated ALLOWED_ORIGINS if individual vars not set
        if not origins and self.ALLOWED_ORIGINS:
            origins = [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
        
        # Default for development if no origins specified
        if not origins:
            return ["*"]  # Allow all origins if none specified (dev only)

        # Add environment-specific defaults
        if self.APP_ENV == Environment.STAGING:
            # Add staging frontend URLs
            default_staging = [
                "https://ali-frontend-staging.vercel.app",
                "https://staging.ali-app.com",  # Custom staging domain
            ]
            origins.extend([url for url in default_staging if url not in origins])
        elif self.APP_ENV == Environment.PRODUCTION:
            # Add production frontend URLs
            default_production = [
                "https://ali-frontend.vercel.app",
                "https://app.ali.com",  # Custom production domain
                "https://ali.com",
            ]
            origins.extend([url for url in default_production if url not in origins])

        return origins

    # Logging Configuration
    LOG_DIR: Path = Field(default=Path("./logs"), env="LOG_DIR")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(default="console", env="LOG_FORMAT")

    # Rate Limiting
    RATE_LIMIT_DEFAULT: str = Field(
        default="1000 per day,200 per hour", env="RATE_LIMIT_DEFAULT"
    )
    RATE_LIMIT_CHAT: str = Field(default="100 per minute", env="RATE_LIMIT_CHAT")
    RATE_LIMIT_CHAT_STREAM: str = Field(
        default="50 per minute", env="RATE_LIMIT_CHAT_STREAM"
    )
    RATE_LIMIT_MESSAGES: str = Field(
        default="100 per minute", env="RATE_LIMIT_MESSAGES"
    )
    RATE_LIMIT_REGISTER: str = Field(default="20 per hour", env="RATE_LIMIT_REGISTER")
    RATE_LIMIT_LOGIN: str = Field(default="50 per minute", env="RATE_LIMIT_LOGIN")
    RATE_LIMIT_ROOT: str = Field(default="50 per minute", env="RATE_LIMIT_ROOT")
    RATE_LIMIT_HEALTH: str = Field(default="100 per minute", env="RATE_LIMIT_HEALTH")

    # Langfuse Configuration
    LANGFUSE_PUBLIC_KEY: str = Field(default="", env="LANGFUSE_PUBLIC_KEY")
    LANGFUSE_SECRET_KEY: str = Field(default="", env="LANGFUSE_SECRET_KEY")
    LANGFUSE_HOST: str = Field(
        default="https://cloud.langfuse.com", env="LANGFUSE_HOST"
    )

    # Agno Agent Configuration
    LLM_API_KEY: str = Field(default="", env="LLM_API_KEY")
    LLM_MODEL: str = Field(default="gpt-4o-mini", env="LLM_MODEL")
    DEFAULT_LLM_TEMPERATURE: float = Field(default=0.2, env="DEFAULT_LLM_TEMPERATURE")
    MAX_TOKENS: int = Field(default=2000, env="MAX_TOKENS")
    MAX_LLM_CALL_RETRIES: int = Field(default=3, env="MAX_LLM_CALL_RETRIES")

    # JWT Configuration
    JWT_SECRET_KEY: str = Field(
        default="your-super-secret-jwt-key-for-development-change-in-production",
        env="JWT_SECRET_KEY",
    )
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    JWT_ACCESS_TOKEN_EXPIRE_DAYS: int = Field(
        default=30, env="JWT_ACCESS_TOKEN_EXPIRE_DAYS"
    )

    # Firebase Configuration
    FIREBASE_PROJECT_ID: str = Field(default="", env="FIREBASE_PROJECT_ID")
    FIREBASE_CREDENTIALS_PATH: str = Field(default="", env="FIREBASE_CREDENTIALS_PATH")
    FIREBASE_STORAGE_BUCKET: str = Field(default="", env="FIREBASE_STORAGE_BUCKET")
    FIREBASE_REGION: str = Field(default="us-central1", env="FIREBASE_REGION")

    # Qdrant Configuration
    QDRANT_URL: str = Field(default="http://localhost:6333", env="QDRANT_URL")
    QDRANT_API_KEY: str = Field(default="", env="QDRANT_API_KEY")
    QDRANT_COLLECTION_NAME: str = Field(
        default="documents", env="QDRANT_COLLECTION_NAME"
    )

    # Evolution API Configuration (WhatsApp)
    EVOLUTION_API_URL: str = Field(default="", env="EVOLUTION_API_URL")
    EVOLUTION_INSTANCE: str = Field(default="", env="EVOLUTION_INSTANCE")
    EVOLUTION_API_KEY: str = Field(default="", env="EVOLUTION_API_KEY")

    # Rate Limiting Endpoints
    @property
    def RATE_LIMIT_ENDPOINTS(self) -> dict:
        """Get rate limit configuration for endpoints."""
        return {
            "default": [self.RATE_LIMIT_DEFAULT],
            "chat": [self.RATE_LIMIT_CHAT],
            "chat_stream": [self.RATE_LIMIT_CHAT_STREAM],
            "messages": [self.RATE_LIMIT_MESSAGES],
            "register": [self.RATE_LIMIT_REGISTER],
            "login": [self.RATE_LIMIT_LOGIN],
            "root": [self.RATE_LIMIT_ROOT],
            "health": [self.RATE_LIMIT_HEALTH],
        }

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()
