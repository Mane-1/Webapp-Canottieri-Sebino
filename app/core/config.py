# app/core/config.py
import os
from dotenv import load_dotenv

# In locale carica .env; su Render le env var sono già disponibili
load_dotenv()

class Settings:
    SECRET_KEY: str = os.getenv("SECRET_KEY", "un-segreto-di-default-non-sicuro")
    DATABASE_URL: str = os.getenv("DATABASE_URL")

settings = Settings()
