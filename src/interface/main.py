"""
interface/main.py
-----------------
Punto de entrada para ejecución por consola 
"""

import sys
import io
from pathlib import Path
from tabulate import tabulate
from dotenv import load_dotenv

# Asegurar que el directorio src está en el path para importaciones limpias
# Como estamos en src/interface, el parent es src.
sys.path.append(str(Path(__file__).parent.parent))

load_dotenv()

# Forzar UTF-8 en consola para evitar errores con emojis/caracteres especiales
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from infrastructure.azure_adapter import AzureNLPAdapter
from infrastructure.excel_adapter import ExcelAdapter
from services.analysis_service import AnalysisService

def imprimir_tabla_resultados(df):
    """Presentación formateada en consola."""
    print("\n" + "═" * 80)
    print("  RESULTADOS DEL ANÁLISIS NLP - STEAM (MODO CONSOLA)")
    print("═" * 80)

    tabla = []
    for _, fila in df.iterrows():
        iconos = {"positive": "(+)", "negative": "(-)", "neutral": "(.)", "mixed": "(~)"}
        icono = iconos.get(fila["sentimiento"], "(?)")
        tabla.append([
            icono,
            fila.get("id", ""),
            fila.get("juego", "")[:20],
            fila["sentimiento_esp"].upper(),
            f"{fila['afinidad_positiva']:.0%}",
            f"{fila['afinidad_negativa']:.0%}",
            fila["etiquetas"][:50] + ("..." if len(fila["etiquetas"]) > 50 else ""),
        ])

    encabezados = ["", "ID", "Juego", "Sentimiento", "Afinidad +", "Afinidad -", "Etiquetas"]
    print(tabulate(tabla, headers=encabezados, tablefmt="rounded_outline"))

def main():
    # 1. Configurar Rutas (Relativas a la raíz del proyecto)
    # Buscamos la carpeta 'data' subiendo dos niveles desde src/interface/
    ROOT = Path(__file__).parent.parent.parent
    input_path = ROOT / "data" / "comentarios_steam.xlsx"
    output_path = ROOT / "data" / "resultados_nlp.xlsx"

    if not input_path.exists():
        print(f"[ERROR] No se encuentra el archivo {input_path}")
        print("Ejecuta 'python src/utils/genera_datos.py' primero.")
        return

    # 2. Inicializar Capas
    print("INFO: Inicializando servicios...")
    azure_adapter = AzureNLPAdapter() # Toma credenciales de .env
    excel_adapter = ExcelAdapter()
    service = AnalysisService(azure_adapter)

    # 3. Flujo de Ejecución
    try:
        # Carga
        df = excel_adapter.cargar_comentarios(str(input_path), {"id", "juego", "usuario", "comentario"})
        
        # Procesamiento
        print(f"INFO: Procesando {len(df)} comentarios con Azure...")
        df_resultado = service.procesar_dataframe(df)

        # Presentación
        imprimir_tabla_resultados(df_resultado)
        
        # Resumen
        stats = service.generar_resumen_estadistico(df_resultado)
        print(f"\nRESUMEN:")
        print(f"   Total : {stats['total']}")
        print(f"   Pos   : {stats['positivos']} ({stats['positivos']/stats['total']:.0%})")
        print(f"   Neg   : {stats['negativos']} ({stats['negativos']/stats['total']:.0%})")

        # Persistencia
        excel_adapter.guardar_comentarios(df_resultado, str(output_path))
        print(f"\n[OK] Análisis completado. Resultados guardados en {output_path}")

    except Exception as e:
        print(f"\n[ERROR] Ocurrió un error: {e}")

if __name__ == "__main__":
    main()
