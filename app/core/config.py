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


# Load appropriate .env file based on environment
def load_env_file():
    """Load environment-specific .env file."""
    env = get_environment()
    print(f"Loading environment: {env}")
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

    # Define env files in priority order
    env_files = [
        os.path.join(base_dir, f".env.{env.value}.local"),
        os.path.join(base_dir, f".env.{env.value}"),
        os.path.join(base_dir, ".env.local"),
        os.path.join(base_dir, ".env"),
    ]

    # Load the first env file that exists
    for env_file in env_files:
        if os.path.isfile(env_file):
            load_dotenv(dotenv_path=env_file)
            print(f"Loaded environment from {env_file}")
            return env_file

    # Fall back to default if no env file found
    return None


ENV_FILE = load_env_file()


# Parse list values from environment variables
def parse_list_from_env(env_key, default=None):
    """Parse a comma-separated list from an environment variable."""
    value = os.getenv(env_key)
    if not value:
        return default or []

    # Remove quotes if they exist
    value = value.strip("\"'")
    # Handle single value case
    if "," not in value:
        return [value]
    # Split comma-separated values
    return [item.strip() for item in value.split(",") if item.strip()]


# Parse dict of lists from environment variables with prefix
def parse_dict_of_lists_from_env(prefix, default_dict=None):
    """Parse dictionary of lists from environment variables with a common prefix."""
    result = default_dict or {}

    # Look for all env vars with the given prefix
    for key, value in os.environ.items():
        if key.startswith(prefix):
            endpoint = key[len(prefix):].lower()  # Extract endpoint name
            # Parse the values for this endpoint
            if value:
                value = value.strip("\"'")
                if "," in value:
                    result[endpoint] = [item.strip()
                                        for item in value.split(",") if item.strip()]
                else:
                    result[endpoint] = [value]

    return result


from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Environment
    ENVIRONMENT: Environment = Field(default_factory=get_environment)
    
    # Application Settings
    PROJECT_NAME: str = Field(default="FastAPI LangGraph Template", env="PROJECT_NAME")
    VERSION: str = Field(default="1.0.0", env="VERSION")
    DESCRIPTION: str = Field(default="A production-ready FastAPI template with LangGraph and Langfuse integration", env="DESCRIPTION")
    API_V1_STR: str = Field(default="/api/v1", env="API_V1_STR")
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # CORS Settings
    ALLOWED_ORIGINS: str = Field(default="*", env="ALLOWED_ORIGINS")
    
    @property
    def allowed_origins_list(self) -> list[str]:
        if not self.ALLOWED_ORIGINS or self.ALLOWED_ORIGINS.strip() == "":
            return ["*"]
        # Remove quotes if they exist
        value = self.ALLOWED_ORIGINS.strip("\"'")
        # Handle single value case
        if "," not in value:
            return [value]
        # Split comma-separated values
        return [item.strip() for item in value.split(",") if item.strip()]
    
    # Langfuse Configuration
    LANGFUSE_PUBLIC_KEY: str = Field(default="", env="LANGFUSE_PUBLIC_KEY")
    LANGFUSE_SECRET_KEY: str = Field(default="", env="LANGFUSE_SECRET_KEY")
    LANGFUSE_HOST: str = Field(default="https://cloud.langfuse.com", env="LANGFUSE_HOST")
    
    # LangGraph Configuration
    LLM_API_KEY: str = Field(default="", env="LLM_API_KEY")
    LLM_MODEL: str = Field(default="gpt-4o-mini", env="LLM_MODEL")
    DEFAULT_LLM_TEMPERATURE: float = Field(default=0.2, env="DEFAULT_LLM_TEMPERATURE")
    MAX_TOKENS: int = Field(default=2000, env="MAX_TOKENS")
    MAX_LLM_CALL_RETRIES: int = Field(default=3, env="MAX_LLM_CALL_RETRIES")
    
    # JWT Configuration
    JWT_SECRET_KEY: str = Field(default="", env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    JWT_ACCESS_TOKEN_EXPIRE_DAYS: int = Field(default=30, env="JWT_ACCESS_TOKEN_EXPIRE_DAYS")
    
    # Logging Configuration
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(default="json", env="LOG_FORMAT")
    
    # Postgres Configuration
    POSTGRES_URL: str = Field(default="", env="POSTGRES_URL")
    POSTGRES_POOL_SIZE: int = Field(default=20, env="POSTGRES_POOL_SIZE")
    POSTGRES_MAX_OVERFLOW: int = Field(default=10, env="POSTGRES_MAX_OVERFLOW")
    
    # Rate Limiting Configuration
    RATE_LIMIT_DEFAULT: str = Field(default="200 per day,50 per hour", env="RATE_LIMIT_DEFAULT")
    
    # Elasticsearch Configuration
    ELASTICSEARCH_URL: str = Field(default="", env="ELASTICSEARCH_URL")
    ELASTICSEARCH_API_KEY: str = Field(default="", env="ELASTICSEARCH_API_KEY")
    
    # RAG Configuration
    RAG_INDEX_NAME: str = Field(default="agua-clara-ms", env="RAG_INDEX_NAME")
    RAG_EMBEDDING_MODEL: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", env="RAG_EMBEDDING_MODEL")
    RAG_CHUNK_SIZE: int = Field(default=1000, env="RAG_CHUNK_SIZE")
    RAG_CHUNK_OVERLAP: int = Field(default=200, env="RAG_CHUNK_OVERLAP")
    RAG_MAX_RESULTS: int = Field(default=5, env="RAG_MAX_RESULTS")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        
    @property
    def LOG_DIR(self) -> Path:
        return Path(os.getenv("LOG_DIR", "logs"))
        
    @property
    def CHECKPOINT_TABLES(self) -> list[str]:
        return ["checkpoint_blobs", "checkpoint_writes", "checkpoints"]


# Create settings instance
settings = Settings()
