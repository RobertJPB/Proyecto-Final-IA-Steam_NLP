"""
infrastructure/azure_adapter.py
------------------------------
Adaptador para el servicio Azure AI Language.
"""

import os
from typing import List, Dict, Any
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from core.constants import AZURE_BATCH_SIZE

class AzureNLPAdapter:
    def __init__(self, key: str = None, endpoint: str = None):
        """
        Inicializa el adaptador de Azure. Si no se proveen credenciales, 
        intenta cargarlas del entorno.
        """
        self.key = key or os.getenv("AZURE_LANGUAGE_KEY")
        self.endpoint = endpoint or os.getenv("AZURE_LANGUAGE_ENDPOINT")
        self._client = None

    @property
    def client(self) -> TextAnalyticsClient:
        if not self._client:
            if not self.key or not self.endpoint:
                raise ValueError("ERROR: Faltan credenciales de Azure AI Language.")
            self._client = TextAnalyticsClient(
                endpoint=self.endpoint, 
                credential=AzureKeyCredential(self.key)
            )
        return self._client

    def analizar_sentimientos(self, textos: List[str]) -> List[Dict[str, Any]]:
        """Llamada directa al API de Sentimiento de Azure."""
        resultados = []
        for i in range(0, len(textos), AZURE_BATCH_SIZE):
            lote = textos[i : i + AZURE_BATCH_SIZE]
            respuesta = self.client.analyze_sentiment(lote, language="es")
            
            for doc in respuesta:
                if doc.is_error:
                    resultados.append({
                        "sentimiento": "error",
                        "afinidad_positiva": 0.0,
                        "afinidad_negativa": 0.0,
                        "afinidad_neutral": 0.0,
                        "error_detalle": doc.error.message,
                    })
                else:
                    scores = doc.confidence_scores
                    resultados.append({
                        "sentimiento": doc.sentiment,
                        "afinidad_positiva": round(scores.positive, 4),
                        "afinidad_negativa": round(scores.negative, 4),
                        "afinidad_neutral":  round(scores.neutral, 4),
                        "error_detalle": None,
                    })
        return resultados

    def extraer_palabras_clave(self, textos: List[str]) -> List[List[str]]:
        """Llamada directa al API de Key Phrases de Azure."""
        etiquetas_por_texto = []
        for i in range(0, len(textos), AZURE_BATCH_SIZE):
            lote = textos[i : i + AZURE_BATCH_SIZE]
            respuesta = self.client.extract_key_phrases(lote, language="es")
            
            for doc in respuesta:
                if doc.is_error:
                    etiquetas_por_texto.append([])
                else:
                    etiquetas_por_texto.append(doc.key_phrases[:10])
        return etiquetas_por_texto
