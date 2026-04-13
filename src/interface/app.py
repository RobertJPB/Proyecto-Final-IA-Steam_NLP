"""
interface/app.py
----------------
INTERFAZ WEB DE USUARIO (GUI) CON STREAMLIT - REFACCIÓN POR CAPAS
"""

import os
import io
import sys
from pathlib import Path

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from dotenv import load_dotenv

# Asegurar que el directorio src está en el path para importaciones limpias
# Como estamos en src/interface, el parent es src.
sys.path.append(str(Path(__file__).parent.parent))

from infrastructure.azure_adapter import AzureNLPAdapter
from infrastructure.steam_adapter import SteamAdapter
from services.analysis_service import AnalysisService

load_dotenv()

# ─────────────────────────────────────────────
# CONFIGURACIÓN DE PÁGINA
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="Steam NLP",
    page_icon=None,
    layout="wide",
)

# ─────────────────────────────────────────────
# INICIALIZACIÓN DE SERVICIOS (SINGLETONS)
# ─────────────────────────────────────────────

@st.cache_resource
def get_adapters(key, endpoint):
    azure = AzureNLPAdapter(key=key, endpoint=endpoint)
    steam = SteamAdapter()
    service = AnalysisService(azure)
    return azure, steam, service

# ==============================================================================
# 1. DISEÑO DE LA INTERFAZ (CSS)
# ==============================================================================

st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    .metric-card {
        background: #1a1f2e;
        border-radius: 12px;
        padding: 20px 24px;
        text-align: center;
    }
    .metric-number { font-size: 2.2rem; font-weight: 700; }
    .metric-label  { font-size: 0.85rem; color: #aaa; margin-top: 4px; }
    .tag {
        display: inline-block;
        background: #1f3a5f;
        color: #7ec8e3;
        border-radius: 6px;
        padding: 2px 10px;
        margin: 2px 3px;
        font-size: 0.78rem;
    }
    .badge-pos { background:#1a3d2b; color:#4caf82; border-radius:6px; padding:3px 10px; font-weight:600; }
    .badge-neg { background:#3d1a1a; color:#e57373; border-radius:6px; padding:3px 10px; font-weight:600; }
    .badge-neu { background:#2a2a1a; color:#f0c040; border-radius:6px; padding:3px 10px; font-weight:600; }
    .badge-mix { background:#2a1a3d; color:#c084fc; border-radius:6px; padding:3px 10px; font-weight:600; }
    .badge-err { background:#3d2a1a; color:#fb923c; border-radius:6px; padding:3px 10px; font-weight:600; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────

st.title("Steam NLP")
st.caption("Analisis de sentimiento y extraccion de etiquetas usando Azure AI Language (Arquitectura por Capas)")
st.divider()

# ─────────────────────────────────────────────
# SIDEBAR — CONFIGURACIÓN
# ─────────────────────────────────────────────

with st.sidebar:
    st.header("Configuracion")
    st.subheader("Azure AI Language")

    key_env      = os.getenv("AZURE_LANGUAGE_KEY", "")
    endpoint_env = os.getenv("AZURE_LANGUAGE_ENDPOINT", "")

    azure_key      = st.text_input("API Key", value=key_env, type="password", placeholder="tu_clave_aqui")
    azure_endpoint = st.text_input("Endpoint", value=endpoint_env, placeholder="https://tu-recurso.cognitiveservices.azure.com/")

    if azure_key and azure_endpoint:
        # Inyectamos las credenciales en los adaptadores
        azure_adapter, steam_adapter, analysis_service = get_adapters(azure_key, azure_endpoint)
        st.success("OK: Capas inicializadas")
    else:
        st.warning("ADVERTENCIA: Ingresa tus credenciales de Azure para continuar.")
        st.stop() # Detener ejecución si no hay credenciales

    st.divider()

    with st.expander("Resolucion del Caso Steam", expanded=True):
        st.markdown("""
        **Estructura Refactorizada**:
        1.  **Dominio**: Constantes centralizadas.
        2.  **Infraestructura**: Adaptadores para Azure y Steam.
        3.  **Servicio**: Orquestación limpia del análisis.
        4.  **Presentación**: Streamlit simplificado.
        """)

# ==============================================================================
# 2. SECCION DE TAREAS Y NAVEGACION (TABS)
# ==============================================================================

tab_steam, tab_upload, tab_manual, tab_resultados = st.tabs([
    "Steam (API real)",
    "Cargar Excel",
    "Comentario manual",
    "Resultados",
])

# ── Helpers Visuales ──────────────────────────

def badge_sentimiento(sent: str) -> str:
    clases = {"positive": "badge-pos", "negative": "badge-neg", "neutral": "badge-neu", "mixed": "badge-mix", "error": "badge-err"}
    labels = {"positive": "POSITIVO", "negative": "NEGATIVO", "neutral": "NEUTRAL", "mixed": "MIXTO", "error": "ERROR"}
    return f'<span class="{clases.get(sent, "badge-neu")}">{labels.get(sent, sent.upper())}</span>'

def tags_html(etiquetas_str: str) -> str:
    if not etiquetas_str: return "—"
    return "".join(f'<span class="tag">{t.strip()}</span>' for t in etiquetas_str.split(",") if t.strip())

def mostrar_resultados_ui(df: pd.DataFrame):
    """Renderiza métricas, tabla y gráficos."""
    st.session_state["df_resultados"] = df
    stats = analysis_service.generar_resumen_estadistico(df)

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f'<div class="metric-card"><div class="metric-number">{stats["total"]}</div><div class="metric-label">Comentarios</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><div class="metric-number" style="color:#4caf82">{stats["positivos"]} <small style="font-size:1rem">({stats["positivos"]/stats["total"]:.0%})</small></div><div class="metric-label">Positivos</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><div class="metric-number" style="color:#e57373">{stats["negativos"]} <small style="font-size:1rem">({stats["negativos"]/stats["total"]:.0%})</small></div><div class="metric-label">Negativos</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="metric-card"><div class="metric-number" style="color:#7ec8e3">{stats["promedio_etiquetas"]:.1f}</div><div class="metric-label">Etiquetas prom.</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Resultados detallados")

    for _, fila in df.iterrows():
        with st.container():
            col_sent, col_juego, col_usuario, col_scores = st.columns([2, 2, 2, 3])
            col_sent.markdown(badge_sentimiento(fila["sentimiento"]), unsafe_allow_html=True)
            col_juego.markdown(f"**{fila.get('juego','—')}**")
            col_usuario.markdown(f"ID Usuario: {fila.get('usuario','—')}")
            col_scores.markdown(f"Pos: `{fila['afinidad_positiva']:.0%}` &nbsp; Neg: `{fila['afinidad_negativa']:.0%}`")
            st.markdown(f"> {fila['comentario']}")
            st.markdown(tags_html(fila["etiquetas"]), unsafe_allow_html=True)
            st.divider()

    # Visualizaciones (Matplotlib)
    st.subheader("Visualizaciones")
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    fig.patch.set_facecolor("#0e1117")
    for ax in axes:
        ax.set_facecolor("#1a1f2e")
        ax.tick_params(colors="white")
        for spine in ax.spines.values(): spine.set_edgecolor("#333")

    # Gráfico 1
    conteo = df["sentimiento_esp"].value_counts()
    colores = {"positivo": "#4caf82", "negativo": "#e57373", "neutral": "#f0c040", "mixto": "#c084fc"}
    axes[0].bar(conteo.index, conteo.values, color=[colores.get(s, "#aaa") for s in conteo.index])
    axes[0].set_title("Distribución", color="white")

    # Gráfico 2
    axes[1].plot(df.index, df["afinidad_positiva"], label="Positiva", color="#4caf82")
    axes[1].plot(df.index, df["afinidad_negativa"], label="Negativa", color="#e57373")
    axes[1].legend()
    st.pyplot(fig)

    # Exportar
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Resultados")
    st.download_button("Descargar Excel", output.getvalue(), "resultados.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# ==============================================================================
# 3. LÓGICA DE TABS
# ==============================================================================

with tab_steam:
    st.subheader("Reseñas reales de Steam")
    nombre_juego = st.text_input("Nombre del juego", key="steam_search")
    if st.button("Buscar en Steam"):
        juegos = steam_adapter.buscar_juegos(nombre_juego)
        st.session_state["juegos_encontrados"] = juegos

    if "juegos_encontrados" in st.session_state:
        juegos = st.session_state["juegos_encontrados"]
        if juegos:
            opciones = {f"{j['name']} (ID: {j['appid']})": j for j in juegos}
            seleccion = st.radio("Selecciona juego:", list(opciones.keys()))
            j_sel = opciones[seleccion]
            
            cant = st.slider("Cantidad", 10, 100, 20)
            if st.button("Analizar Reseñas"):
                with st.spinner("Descargando y Analizando..."):
                    df_s = steam_adapter.obtener_reseñas(j_sel["appid"], j_sel["name"], cant)
                    df_res = analysis_service.procesar_dataframe(df_s)
                    mostrar_resultados_ui(df_res)
        else:
            st.warning("No se encontraron resultados.")

with tab_upload:
    archivo = st.file_uploader("Sube Excel", type=["xlsx"])
    if archivo:
        df_up = pd.read_excel(archivo)
        if st.button("Analizar Archivo"):
            with st.spinner("Procesando..."):
                df_res = analysis_service.procesar_dataframe(df_up)
                mostrar_resultados_ui(df_res)

with tab_manual:
    comentario = st.text_area("Comentario individual")
    if st.button("Analizar uno"):
        df_m = pd.DataFrame([{"id":1, "juego":"Manual", "usuario":"User", "comentario":comentario}])
        df_res = analysis_service.procesar_dataframe(df_m)
        mostrar_resultados_ui(df_res)

with tab_resultados:
    if "df_resultados" in st.session_state:
        mostrar_resultados_ui(st.session_state["df_resultados"])
    else:
        st.info("Analiza datos para ver resultados aquí.")
