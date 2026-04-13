"""
infrastructure/steam_adapter.py
------------------------------
Adaptador para la API de Steam (Reviews y Búsqueda).
"""

import time
import requests
import pandas as pd
from typing import List, Dict, Any
from core.constants import (
    STEAM_SEARCH_URL, 
    STEAM_REVIEWS_URL, 
    MAX_STEAM_REVIEWS_BATCH,
    MAX_REVIEW_LENGTH
)

class SteamAdapter:
    def buscar_juegos(self, nombre: str) -> List[Dict[str, Any]]:
        """Busca juegos en Steam y devuelve lista de appid/name."""
        params = {
            "term": nombre,
            "l": "spanish",
            "cc": "US",
        }
        resp = requests.get(STEAM_SEARCH_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("items", [])
        return [{"appid": item["id"], "name": item["name"]} for item in items[:8]]

    def obtener_reseñas(
        self, 
        appid: int, 
        nombre_juego: str, 
        cantidad: int = 50, 
        idioma: str = "spanish"
    ) -> pd.DataFrame:
        """Descarga reseñas de Steam y devuelve un DataFrame."""
        url = STEAM_REVIEWS_URL.format(appid=appid)
        reseñas = []
        cursor = "*"
        intentos = 0
        max_intentos = 10

        while len(reseñas) < cantidad and intentos < max_intentos:
            params = {
                "json": 1,
                "filter": "recent",
                "language": idioma,
                "cursor": cursor,
                "num_per_page": min(MAX_STEAM_REVIEWS_BATCH, cantidad - len(reseñas)),
                "review_type": "all",
                "purchase_type": "all",
            }

            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            if not data.get("success"):
                break

            lote = data.get("reviews", [])
            if not lote:
                break

            for r in lote:
                texto = r.get("review", "").strip()
                if not texto or len(texto) < 15:
                    continue

                reseñas.append({
                    "id":                   len(reseñas) + 1,
                    "juego":                nombre_juego,
                    "usuario":              r.get("author", {}).get("steamid", "anónimo"),
                    "comentario":           texto[:MAX_REVIEW_LENGTH],
                    "votos_utiles":         r.get("votes_up", 0),
                    "clasificacion_steam":  "positivo" if r.get("voted_up") else "negativo",
                    "horas_jugadas":        round(r.get("author", {}).get("playtime_forever", 0) / 60, 1),
                })

                if len(reseñas) >= cantidad:
                    break

            nuevo_cursor = data.get("cursor", "")
            if not nuevo_cursor or nuevo_cursor == cursor:
                break
            cursor = nuevo_cursor
            intentos += 1
            time.sleep(0.5)

        return pd.DataFrame(reseñas)
