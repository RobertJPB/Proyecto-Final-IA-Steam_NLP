"""
utils/genera_datos.py
---------------------
SIMULADOR DE BASE DE DATOS LOCAL (EXCEL)
"""

from pathlib import Path
import pandas as pd

# DIRECTORIO DE DATOS: Aseguramos que exista la carpeta donde Steam guarda sus Excels.
# Subimos 3 niveles desde src/utils/genera_datos.py para llegar a la raíz.
DATA_DIR = Path(__file__).parent.parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

comentarios_muestra = [
    {
        "id": 1,
        "juego": "Elden Ring",
        "usuario": "DragonSlayer99",
        "comentario": "Una obra maestra absoluta. El mundo abierto es impresionante y los jefes son brutalmente difíciles pero satisfactorios. Sin duda el mejor juego del año.",
        "calificacion_estrellas": 5
    },
    {
        "id": 2,
        "juego": "Elden Ring",
        "usuario": "CasualGamer22",
        "comentario": "Demasiado difícil para mi gusto. No tiene modo fácil y los controles son confusos. Me arrepiento de haberlo comprado.",
        "calificacion_estrellas": 2
    },
    {
        "id": 3,
        "juego": "Cyberpunk 2077",
        "usuario": "NeonRider",
        "comentario": "Después de todos los parches está increíble. La historia es profunda, los personajes son memorables y Night City se siente viva. Totalmente recomendado.",
        "calificacion_estrellas": 5
    },
    {
        "id": 4,
        "juego": "Cyberpunk 2077",
        "usuario": "Decepcionado2020",
        "comentario": "El lanzamiento fue un desastre y aunque mejoró, aún tiene bugs. La IA enemiga es terrible y el mundo no reacciona como prometieron.",
        "calificacion_estrellas": 2
    },
    {
        "id": 5,
        "juego": "Hades",
        "usuario": "RoguelikeKing",
        "comentario": "El mejor roguelike que he jugado. Cada run se siente diferente, la música es fantástica y los personajes tienen mucha profundidad. Adictivo al máximo.",
        "calificacion_estrellas": 5
    },
    {
        "id": 6,
        "juego": "FIFA 24",
        "usuario": "FutbolFanatico",
        "comentario": "Básicamente el mismo juego de siempre con jugadores actualizados. El modo Ultimate Team está lleno de micropagos y es imposible competir sin gastar dinero real.",
        "calificacion_estrellas": 1
    },
    {
        "id": 7,
        "juego": "Stardew Valley",
        "usuario": "FarmLife",
        "comentario": "Relajante y encantador. Perfecto para desconectarse del estrés. La comunidad del juego es muy amigable y hay muchísimo contenido por descubrir.",
        "calificacion_estrellas": 5
    },
    {
        "id": 8,
        "juego": "Redfall",
        "usuario": "DeceptionHunter",
        "comentario": "Un completo fraude. Prometieron un shooter cooperativo épico y entregaron algo incompleto, lleno de bugs y con una IA ridícula. No lo compren.",
        "calificacion_estrellas": 1
    },
    {
        "id": 9,
        "juego": "Baldur's Gate 3",
        "usuario": "TableTopRPG",
        "comentario": "Revoluciona el género RPG. Las decisiones importan de verdad, los compañeros tienen personalidades únicas y la historia es épica. Vale cada centavo.",
        "calificacion_estrellas": 5
    },
    {
        "id": 10,
        "juego": "Starfield",
        "usuario": "SpaceExplorer",
        "comentario": "Decepcionante para ser un juego de Bethesda. Los planetas se sienten vacíos, la exploración es aburrida y la historia no engancha. Esperaba mucho más.",
        "calificacion_estrellas": 2
    },
    {
        "id": 11,
        "juego": "Hollow Knight",
        "usuario": "MetroidFan",
        "comentario": "Arte hermoso, gameplay desafiante y una atmósfera única. Un metroidvania perfecto que supera a juegos triple A en diseño y creatividad.",
        "calificacion_estrellas": 5
    },
    {
        "id": 12,
        "juego": "Call of Duty MW3",
        "usuario": "FPSLegend",
        "comentario": "Los servidores son una catástrofe. Lag constante, cheaters en cada partida y el soporte técnico no responde. Para ser un juego de $70 es una vergüenza.",
        "calificacion_estrellas": 1
    },
]

df = pd.DataFrame(comentarios_muestra)
output_path = DATA_DIR / "comentarios_steam.xlsx"
df.to_excel(output_path, index=False)
print(f"OK: Archivo Excel generado con {len(df)} comentarios en {output_path}")
