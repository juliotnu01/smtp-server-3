import os
from pydantic import BaseSettings, EmailStr
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
# This is useful for local development.
# In production, environment variables are typically set directly in the environment or via orchestration.
load_dotenv()

class Settings(BaseSettings):
    # SMTP Server Configuration
    MAIL_SERVER_HOST: str = "localhost"
    MAIL_SERVER_PORT: int = 587
    MAIL_USERNAME: EmailStr
    MAIL_PASSWORD: str
    DEFAULT_FROM_EMAIL: EmailStr

    # API Security (Optional)
    # If you want to protect your API endpoint, generate a secure random string
    # and set it as API_KEY in your .env file.
    # Clients would then need to send this key in an 'X-API-Key' header.
    API_KEY: Optional[str] = None

    # Optional: Project name, version, etc.
    # PROJECT_NAME: str = "FastAPI Email Sender"
    # PROJECT_VERSION: str = "0.1.0"

    class Config:
        # This tells Pydantic to load variables from an .env file if present.
        # However, we are using load_dotenv() explicitly above for more control,
        # but keeping this for reference or if you prefer Pydantic's built-in .env handling.
        # env_file = ".env"
        # env_file_encoding = "utf-8"
        pass

# Instantiate settings
# This instance will be imported by other modules to access configuration values.
settings = Settings()

# Example of how to access settings in other files:
# from app.config import settings
# print(settings.MAIL_SERVER_HOST)
