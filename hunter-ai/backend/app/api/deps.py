import hmac

from fastapi import Depends, Header, HTTPException, status

from app.core.config import Settings, get_settings


def require_actor(
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> str:
    """Autorisation des routes qui modifient un état.

    - Si `API_ACCESS_TOKEN` est défini : jeton Bearer obligatoire.
    - Sinon, en développement/test (usage local) : acteur « local ».
    - Sinon, en production : refus par défaut (valeur prudente).
    """
    expected = settings.api_access_token.get_secret_value()
    if expected:
        provided = (authorization or "").removeprefix("Bearer ").strip()
        if not provided or not hmac.compare_digest(provided, expected):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentification requise")
        return "token"
    if settings.app_env == "production":
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Modification refusée : définissez API_ACCESS_TOKEN en production",
        )
    return "local"
