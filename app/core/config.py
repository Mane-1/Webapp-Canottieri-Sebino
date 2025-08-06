# app/core/config.py
import os
from dotenv import load_dotenv

# Carica le variabili da .env in locale (su Render non serve, perché già in env)
load_dotenv()

class Settings:
    # Se non trovi SECRET_KEY in env, usi questo default temporaneo
    SECRET_KEY: str = os.getenv("SECRET_KEY", "un-secret-di-default")
    DATABASE_URL: str = os.getenv("DATABASE_URL")

settings = Settings()
