"""
services/analysis_service.py
----------------------------
Servicio de aplicación que orquesta el análisis de sentimientos.
"""

import pandas as pd
from typing import Optional
from core.constants import MAPA_SENTIMIENTOS
from infrastructure.azure_adapter import AzureNLPAdapter

class AnalysisService:
    def __init__(self, azure_adapter: AzureNLPAdapter):
        self.azure_adapter = azure_adapter

    def procesar_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Orquesta el análisis de un DataFrame:
        1. Extrae textos.
        2. Llama a Azure (Sentimiento + Palabras Clave).
        3. Enriquece el DataFrame.
        """
        if df.empty:
            return df

        textos = df["comentario"].tolist()

        # 1. Análisis de sentimiento
        sentimientos = self.azure_adapter.analizar_sentimientos(textos)
        
        # 2. Extracción de palabras clave
        palabras_clave = self.azure_adapter.extraer_palabras_clave(textos)

        # 3. Enriquecer DataFrame
        df_resultado = df.copy()
        df_resultado["sentimiento"]       = [s["sentimiento"] for s in sentimientos]
        df_resultado["sentimiento_esp"]   = df_resultado["sentimiento"].map(MAPA_SENTIMIENTOS)
        df_resultado["afinidad_positiva"] = [s["afinidad_positiva"] for s in sentimientos]
        df_resultado["afinidad_negativa"] = [s["afinidad_negativa"] for s in sentimientos]
        df_resultado["afinidad_neutral"]  = [s["afinidad_neutral"]  for s in sentimientos]
        df_resultado["etiquetas"]         = [", ".join(kw) for kw in palabras_clave]
        df_resultado["num_etiquetas"]     = [len(kw) for kw in palabras_clave]

        return df_resultado

    def generar_resumen_estadistico(self, df: pd.DataFrame) -> dict:
        """Calcula métricas generales para visualización."""
        total = len(df)
        if total == 0:
            return {}

        # Asegurar que num_etiquetas sea numérico para el cálculo
        avg_etiquetas = pd.to_numeric(df["num_etiquetas"], errors='coerce').mean()
        
        return {
            "total": total,
            "positivos": (df["sentimiento"] == "positive").sum(),
            "negativos": (df["sentimiento"] == "negative").sum(),
            "neutros":   (df["sentimiento"] == "neutral").sum(),
            "mixtos":    (df["sentimiento"] == "mixed").sum(),
            "total_etiquetas": int(df["num_etiquetas"].sum()),
            "promedio_etiquetas": avg_etiquetas if not pd.isna(avg_etiquetas) else 0.0
        }
    def obtener_top_etiquetas(self, df: pd.DataFrame, top_n: int = 10) -> pd.Series:
        """Extrae y cuenta la frecuencia de cada etiqueta en el DataFrame."""
        todas = []
        for tags in df["etiquetas"].dropna():
            if isinstance(tags, str) and tags.strip():
                todas.extend([t.strip().lower() for t in tags.split(",")])
        
        if not todas:
            return pd.Series(dtype=int)
            
        return pd.Series(todas).value_counts().head(top_n)
