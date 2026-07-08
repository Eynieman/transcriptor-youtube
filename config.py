import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def get_google_api_key():
    """Return the Google API key from the environment or from the local .env file."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        return api_key

    dotenv_path = BASE_DIR / ".env"
    if not dotenv_path.exists():
        return None

    for linea in dotenv_path.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue

        clave, valor = linea.split("=", 1)
        if clave.strip() == "GOOGLE_API_KEY":
            return valor.strip().strip("\"'")

    return None
