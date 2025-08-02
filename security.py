# File: security.py
# Questo file contiene tutte le funzioni e le configurazioni
# relative alla sicurezza, come la gestione delle password.

from passlib.context import CryptContext

# 1. Configurazione del contesto per l'hashing delle password
# Usiamo bcrypt come algoritmo di hashing, che è lo standard di sicurezza attuale.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# 2. Funzioni di verifica e hashing

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica se una password in chiaro corrisponde a una password hashata.

    Args:
        plain_password: La password inserita dall'utente.
        hashed_password: La password salvata nel database.

    Returns:
        True se le password corrispondono, altrimenti False.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Genera l'hash di una password.

    Args:
        password: La password in chiaro da hashare.

    Returns:
        La stringa della password hashata.
    """
    return pwd_context.hash(password)
