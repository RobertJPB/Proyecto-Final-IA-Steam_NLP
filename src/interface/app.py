"""
interface/app.py
----------------
INTERFAZ WEB DE USUARIO (GUI) CON STREAMLIT - 
"""

import os
import io
import sys
from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
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

def load_css():
    css_file = Path(__file__).parent / "style.css"
    if css_file.exists():
        with open(css_file, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────

st.title("Steam NLP Dashboard")
st.caption("Análisis inteligente de sentimientos y extracción de entidades con Azure AI Language")

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
    return f'<span class="badge {clases.get(sent, "badge-neu")}">{labels.get(sent, sent.upper())}</span>'

def tags_html(etiquetas_str: str) -> str:
    if not etiquetas_str: return ""
    return "".join(f'<span class="tag">{t.strip()}</span>' for t in etiquetas_str.split(",") if t.strip())

def mostrar_resultados_ui(df_original: pd.DataFrame, key: str = "default"):
    """Renderiza métricas, tabla y gráficos con Plotly."""
    if df_original.empty:
        st.info("No hay datos para mostrar.")
        return

    # 1. Limpieza Crítica: Eliminar filas fantasma (vacías o sin comentario)
    # Esto evita que índices vacíos de Excel afecten los promedios
    df = df_original.copy()
    df = df.dropna(subset=["comentario"])
    df = df[df["comentario"].astype(str).str.strip() != ""]
    
    if df.empty:
        st.warning("Los datos analizados no contienen comentarios válidos.")
        return

    # Asegurar tipos numéricos para evitar que Plotly los trate como texto o falle el promedio
    for col in ["afinidad_positiva", "afinidad_negativa", "afinidad_neutral", "num_etiquetas"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        else:
            df[col] = 0.0
    
    stats = analysis_service.generar_resumen_estadistico(df)

    # Métricas Premium (Ahora con 6 columnas para incluir Mixtas)
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1: st.markdown(f'<div class="metric-card"><div class="metric-number">{stats["total"]}</div><div class="metric-label">Reseñas</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card"><div class="metric-number" style="color:#4caf82">{stats["positivos"]}</div><div class="metric-label">Positivas</div></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metric-card"><div class="metric-number" style="color:#f0c040">{stats["neutros"]}</div><div class="metric-label">Neutras</div></div>', unsafe_allow_html=True)
    with c4: st.markdown(f'<div class="metric-card"><div class="metric-number" style="color:#a58aff">{stats.get("mixtos", 0)}</div><div class="metric-label">Mixtas</div></div>', unsafe_allow_html=True)
    with c5: st.markdown(f'<div class="metric-card"><div class="metric-number" style="color:#e57373">{stats["negativos"]}</div><div class="metric-label">Negativas</div></div>', unsafe_allow_html=True)
    with c6: st.markdown(f'''
        <div class="metric-card">
            <div class="metric-number" style="color:#7ec8e3">{stats["total_etiquetas"]}</div>
            <div class="metric-label">Total Etiquetas</div>
        </div>
    ''', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Visualizaciones con Plotly (Solo Dona para un diseño más limpio)
    st.subheader("Balance de Probabilidades (IA)")
    
    fig_pie = go.Figure(data=[go.Pie(
        labels=["Positiva", "Negativa", "Neutral"],
        values=[
            df["afinidad_positiva"].mean(),
            df["afinidad_negativa"].mean(),
            df["afinidad_neutral"].mean()
        ],
        hole=0.4,
        marker=dict(colors=["#4caf82", "#e57373", "#f0c040"]),
        textinfo='percent',
        hoverinfo='label+percent+value'
    )])
    
    fig_pie.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)', 
        font_color='white',
        margin=dict(t=20, b=20, l=0, r=0), 
        height=400,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
    )
    st.plotly_chart(fig_pie, use_container_width=True)


    # 5. Análisis Detallado (Filtrable)
    c_h, c_f = st.columns([2, 1])
    with c_h:
        st.markdown('<div class="section-header">Análisis Detallado</div>', unsafe_allow_html=True)
    with c_f:
        filtro = st.selectbox(
            "Filtrar por sentimiento:",
            ["Todos", "Positivo", "Negativo", "Neutral", "Mixto"],
            key=f"filter_{key}"
        )

    # Aplicar Filtro
    df_visible = df.copy()
    if filtro != "Todos":
        mapa_filtro = {"Positivo": "positive", "Negativo": "negative", "Neutral": "neutral", "Mixto": "mixed"}
        df_visible = df_visible[df_visible["sentimiento"] == mapa_filtro[filtro]]

    if df_visible.empty:
        st.info(f"No hay reseñas con sentimiento '{filtro}' para mostrar.")
        return

    for _, fila in df_visible.iterrows():
        sent = fila["sentimiento"]
        st.markdown(f"""
        <div class="result-card {sent}">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <div>{badge_sentimiento(sent)} <b style="margin-left:10px; font-size: 1.1rem;">{fila.get('juego','—')}</b></div>
                <div style="font-size: 0.85rem; color: #aaa;">Usuario ID: {fila.get('usuario','—')}</div>
            </div>
            <p style="font-style: italic; color: #eee; margin: 10px 0;">"{fila['comentario']}"</p>
            <div style="margin: 10px 0;">{tags_html(fila["etiquetas"])}</div>
                <span>Afinidad Positiva: <code style="color:#4caf82">{fila['afinidad_positiva']:.1%}</code></span>
                <span>Afinidad Negativa: <code style="color:#e57373">{fila['afinidad_negativa']:.1%}</code></span>
                <span>Afinidad Neutral: <code style="color:#aaa">{fila['afinidad_neutral']:.1%}</code></span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Exportar
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Resultados")
    st.download_button(
        label="📥 Descargar Reporte Excel",
        data=output.getvalue(),
        file_name="resultados_steam.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key=f"dl_btn_{key}"
    )


# ==============================================================================
# 3. LÓGICA DE TABS
# ==============================================================================

def actualizar_resultados(df_nuevo: pd.DataFrame):
    """Agrega nuevos resultados al historial acumulado."""
    if "df_resultados" not in st.session_state:
        st.session_state["df_resultados"] = df_nuevo
    else:
        st.session_state["df_resultados"] = pd.concat([st.session_state["df_resultados"], df_nuevo], ignore_index=True)

with tab_steam:
    st.subheader("Reseñas reales de Steam")
    
    # Ejemplos sugeridos
    st.markdown("**Ejemplos sugeridos:** `Cyberpunk 2077`, `Elden Ring`, `Hades`, `Hollow Knight`")
    
    nombre_juego = st.text_input("Nombre del juego", key="steam_search", placeholder="Ej: Elden Ring")
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
                    actualizar_resultados(df_res)
                    mostrar_resultados_ui(st.session_state["df_resultados"], key="steam")
        else:
            st.warning("No se encontraron resultados.")

with tab_upload:
    archivo = st.file_uploader("Sube Excel", type=["xlsx"])
    if archivo:
        df_up = pd.read_excel(archivo)
        if st.button("Analizar Archivo"):
            with st.spinner("Procesando..."):
                df_res = analysis_service.procesar_dataframe(df_up)
                actualizar_resultados(df_res)
                mostrar_resultados_ui(st.session_state["df_resultados"], key="upload")

with tab_manual:
    comentario = st.text_area("Comentario individual")
    if st.button("Analizar uno"):
        df_m = pd.DataFrame([{"id":1, "juego":"Manual", "usuario":"User", "comentario":comentario}])
        df_res = analysis_service.procesar_dataframe(df_m)
        actualizar_resultados(df_res)
        mostrar_resultados_ui(st.session_state["df_resultados"], key="manual")

with tab_resultados:
    if "df_resultados" in st.session_state:
        mostrar_resultados_ui(st.session_state["df_resultados"], key="tab_res")
    else:
        st.info("Analiza datos para ver resultados aquí.")
