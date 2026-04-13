# Steam NLP - Análisis de Comentarios con Azure AI Language

**Inteligencia Artificial**  
**Estudiantes:** Robert Junior Plaza Brito, Yolquin Grullon  
**Profesor:** Risaldy Jose Rodriguez Jimenez  


---

## 1. Introducción
Sistema diseñado para automatizar la clasificación de sentimientos y el etiquetado de comentarios en la plataforma Steam. Este proyecto resuelve la problemática de inconsistencias detectadas por el equipo de soporte mediante el uso de modelos de procesamiento de lenguaje natural en la nube.

## 2. Organización del Proyecto

```
steam_nlp/
├── src/
│   ├── core/
│   │   └── constants.py          # Dicccionario de sentimientos 
│   │                                       constantes
│   ├── infrastructure/
│   │   ├── azure_adapter.py      # Conectividad con Azure AI Language
│   │   ├── steam_adapter.py      # Interacción con Web API de Steam
│   │   └── excel_adapter.py      # Manejo de archivos Pandas Excel
│   ├── services/
│   │   └── analysis_service.py   # Orquestador principal de lógica
│   ├── interface/
│   │   ├── app.py                # Interfaz Web (Streamlit)
│   │   ├── main.py               # Interfaz de Consola (CLI)
│   │   └── style.css             # Estilos de la aplicación
│   └── utils/
│       └── genera_datos.py       # Herramienta de datos de 
│                                           prueba
├── data/
│   ├── comentarios_steam.xlsx    # Datos de entrada
│   └── resultados_nlp.xlsx       # Analítica procesada
│
├── .env                          # Credenciales de API (Azure)

```

## 3. Contexto de la Problemática (Caso 2.2.1)
El sistema aborda específicamente los siguientes puntos críticos reportados por Steam:
*   **Inconsistencia en clasificación**: Sustituimos la IA anterior por Azure AI Language para mayor precisión.
*   **Medición de Afinidad**: Obtenemos porcentajes exactos de positividad y negatividad.
*   **Generación de Etiquetas**: Extracción automática de frases clave para mejorar las búsquedas.
*   **Gestión de Excel**: Soporte nativo para leer y escribir en bases de datos Excel mediante Pandas.

## 4. Resolución Tecnológica

### Inteligencia Artificial (Azure Cloud)
Utilizamos modelos avanzados de Microsoft Azure para realizar el análisis de sentimiento y la extracción de palabras clave. Esto permite que el sistema "entienda" el contexto de las reseñas sin intervención manual.

### Manejo de Datos (Pandas)
Utilizamos **Pandas** para procesar los DataFrames de forma eficiente. Esto garantiza que la transición entre el archivo Excel estático y el análisis dinámico sea fluida y sin errores de formato.

### Interfaz de Usuario (Streamlit)
El frontend web permite al equipo de soporte realizar búsquedas en vivo de juegos, analizar archivos subidos y visualizar la analítica mediante gráficos generados por **Matplotlib**.

## 5. Instrucciones de Ejecución

1. Abrir la carpeta en **Visual Studio Code**.
2. Presionar **F5** para iniciar la **Interfaz Web (Web App)**.
3. El programa se abrirá automáticamente en `localhost:8501`.
