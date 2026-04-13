"""
infrastructure/excel_adapter.py
------------------------------
Adaptador para la persistencia en archivos Excel (Pandas).
"""

import pandas as pd
from typing import Set

class ExcelAdapter:
    @staticmethod
    def cargar_comentarios(ruta_excel: str, columnas_requeridas: Set[str] = None) -> pd.DataFrame:
        """Carga un Excel y opcionalmente valida columnas."""
        df = pd.read_excel(ruta_excel)
        if columnas_requeridas and not columnas_requeridas.issubset(df.columns):
            raise ValueError(
                f"❌ El Excel debe tener las columnas: {columnas_requeridas}\n"
                f"   Columnas encontradas: {set(df.columns)}"
            )
        return df

    @staticmethod
    def guardar_comentarios(df: pd.DataFrame, ruta_salida: str):
        """Guarda un DataFrame en Excel."""
        df.to_excel(ruta_salida, index=False)
