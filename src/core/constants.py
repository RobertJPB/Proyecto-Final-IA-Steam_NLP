"""
core/constants.py
-----------------
Constantes globales del sistema.
"""

MAPA_SENTIMIENTOS = {
    "positive": "positivo",
    "negative": "negativo",
    "neutral":  "neutral",
    "mixed":    "mixto",
    "error":    "error",
}

# Configuración de Steam API
STEAM_SEARCH_URL = "https://store.steampowered.com/api/storesearch/"
STEAM_REVIEWS_URL = "https://store.steampowered.com/appreviews/{appid}"

# Configuración de límites
MAX_STEAM_REVIEWS_BATCH = 100
AZURE_BATCH_SIZE = 10
MAX_REVIEW_LENGTH = 1000
