"""
app.py
------
INTERFAZ WEB DE USUARIO (GUI) CON STREAMLIT
"""

import os
import io
import sys
from pathlib import Path

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from dotenv import load_dotenv

# Permitir importar analizador_steam desde el mismo directorio
sys.path.append(str(Path(__file__).parent))
from analizador_steam import (
    crear_cliente_azure,
    analizar_sentimientos,
    extraer_palabras_clave,
    MAPA_SENTIMIENTOS,
)
from obtener_reseñas import buscar_juego, obtener_reseñas

load_dotenv()

# ─────────────────────────────────────────────
# CONFIGURACIÓN DE PÁGINA
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="Steam NLP",
    page_icon=None,
    layout="wide",
)

# ==============================================================================
# 1. DISEÑO DE LA INTERFAZ (CSS)
# ==============================================================================
# Personalizamos el aspecto visual mediante CSS inyectado para lograr mas sobriedad.

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
st.caption("Analisis de sentimiento y extraccion de etiquetas usando Azure AI Language")
st.divider()

# ─────────────────────────────────────────────
# SIDEBAR — CONFIGURACIÓN
# ─────────────────────────────────────────────

with st.sidebar:
    st.header("Configuracion")

    # Credenciales Azure
    st.subheader("Azure AI Language")

    key_env      = os.getenv("AZURE_LANGUAGE_KEY", "")
    endpoint_env = os.getenv("AZURE_LANGUAGE_ENDPOINT", "")

    azure_key      = st.text_input("API Key", value=key_env, type="password", placeholder="tu_clave_aqui")
    azure_endpoint = st.text_input("Endpoint", value=endpoint_env, placeholder="https://tu-recurso.cognitiveservices.azure.com/")

    if azure_key and azure_endpoint:
        os.environ["AZURE_LANGUAGE_KEY"]      = azure_key
        os.environ["AZURE_LANGUAGE_ENDPOINT"] = azure_endpoint
        st.success("OK: Credenciales listas")
    else:
        st.warning("ADVERTENCIA: Ingresa tus credenciales de Azure para continuar.")

    st.divider()

    with st.expander("Resolucion del Caso Steam", expanded=True):
        st.markdown("""
        Este sistema resuelve los problemas planteados por Steam:

        1.  **Inconsistencias**: Sustituimos la IA antigua por **Azure AI Language** (Basada en Transformers), lo que garantiza una comprensión profunda del contexto y elimina errores de clasificación.
        2.  **Afinidad**: El sistema captura el **puntaje de confianza** exacto de cada sentimiento, permitiendo una clasificación precisa.
        3.  **Etiquetado**: Implementamos **Key Phrase Extraction** para identificar palabras clave de forma automática sin intervención del usuario.
        4.  **Base de Datos**: Total compatibilidad con **Excel** a través de Pandas para lectura y exportación.
        5.  **Automatización**: Pipeline listo para procesar comentarios en tiempo real.
        """)

# ==============================================================================
# 2. SECCION DE TAREAS Y NAVEGACION (TABS)
# ==============================================================================
# Organizamos el programa en pestañas para separar las fuentes de datos.

tab_steam, tab_upload, tab_manual, tab_resultados = st.tabs([
    "Steam (API real)",
    "Cargar Excel",
    "Comentario manual",
    "Resultados",
])

# ── Helpers ──────────────────────────────────

def badge_sentimiento(sent: str) -> str:
    clases = {
        "positive": "badge-pos", "negativo": "badge-neg",
        "negative": "badge-neg", "neutral":  "badge-neu",
        "mixed":    "badge-mix", "error":    "badge-err",
    }
    labels = {
        "positive": "POSITIVO", "negative": "NEGATIVO",
        "neutral":  "NEUTRAL",  "mixed":    "MIXTO",
        "error":    "ERROR",
    }
    cls = clases.get(sent, "badge-neu")
    lbl = labels.get(sent, sent.upper())
    return f'<span class="{cls}">{lbl}</span>'


def tags_html(etiquetas_str: str) -> str:
    if not etiquetas_str:
        return "—"
    return "".join(f'<span class="tag">{t.strip()}</span>' for t in etiquetas_str.split(",") if t.strip())


def procesar_df(df: pd.DataFrame) -> pd.DataFrame | None:
    """Llama a Azure y devuelve el DataFrame enriquecido."""
    if not (azure_key and azure_endpoint):
        st.error("❌ Configura tus credenciales de Azure en el panel lateral.")
        return None

    try:
        client = crear_cliente_azure()
    except Exception as e:
        st.error(f"❌ No se pudo conectar a Azure: {e}")
        return None

    textos = df["comentario"].tolist()

    with st.spinner("Analizando sentimientos..."):
        sentimientos = analizar_sentimientos(client, textos)

    with st.spinner("Extrayendo palabras clave..."):
        palabras_clave = extraer_palabras_clave(client, textos)

    df = df.copy()
    df["sentimiento"]       = [s["sentimiento"] for s in sentimientos]
    df["sentimiento_esp"]   = df["sentimiento"].map(MAPA_SENTIMIENTOS)
    df["afinidad_positiva"] = [s["afinidad_positiva"] for s in sentimientos]
    df["afinidad_negativa"] = [s["afinidad_negativa"] for s in sentimientos]
    df["afinidad_neutral"]  = [s["afinidad_neutral"]  for s in sentimientos]
    df["etiquetas"]         = [", ".join(kw) for kw in palabras_clave]
    df["num_etiquetas"]     = [len(kw) for kw in palabras_clave]
    return df


def mostrar_resultados(df: pd.DataFrame):
    """Renderiza métricas, tabla y gráficos."""
    st.session_state["df_resultados"] = df

    total     = len(df)
    positivos = (df["sentimiento"] == "positive").sum()
    negativos = (df["sentimiento"] == "negative").sum()
    neutros   = (df["sentimiento"] == "neutral").sum()
    avg_tags  = df["num_etiquetas"].mean()

    # ==============================================================================
    # 3. COMPONENTES VISUALES (METRICAS Y GRAFICOS)
    # ==============================================================================
    # Mostramos los resultados de forma analitica siguiendo el caso de estudio.
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-number">{total}</div>
            <div class="metric-label">Comentarios</div></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-number" style="color:#4caf82">{positivos} <small style="font-size:1rem">({positivos/total:.0%})</small></div>
            <div class="metric-label">Positivos (+)</div></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-number" style="color:#e57373">{negativos} <small style="font-size:1rem">({negativos/total:.0%})</small></div>
            <div class="metric-label">Negativos (-)</div></div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-number" style="color:#7ec8e3">{avg_tags:.1f}</div>
            <div class="metric-label">Etiquetas promedio</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Tabla de resultados detallados
    st.subheader("Resultados detallados")

    for _, fila in df.iterrows():
        with st.container():
            col_sent, col_juego, col_usuario, col_scores = st.columns([2, 2, 2, 3])
            col_sent.markdown(badge_sentimiento(fila["sentimiento"]), unsafe_allow_html=True)
            col_juego.markdown(f"**{fila.get('juego','—')}**")
            col_usuario.markdown(f"ID Usuario: {fila.get('usuario','—')}")
            col_scores.markdown(
                f"Pos: `{fila['afinidad_positiva']:.0%}` &nbsp; Neg: `{fila['afinidad_negativa']:.0%}`"
            )

            st.markdown(f"> {fila['comentario']}")
            st.markdown(tags_html(fila["etiquetas"]), unsafe_allow_html=True)
            st.divider()

    # Visualizaciones
    st.subheader("Visualizaciones")
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    fig.patch.set_facecolor("#0e1117")

    for ax in axes:
        ax.set_facecolor("#1a1f2e")
        ax.tick_params(colors="white")
        ax.xaxis.label.set_color("white")
        ax.yaxis.label.set_color("white")
        ax.title.set_color("white")
        for spine in ax.spines.values():
            spine.set_edgecolor("#333")

    # Gráfico 1: Distribución de sentimientos
    conteo  = df["sentimiento_esp"].value_counts()
    colores = {"positivo": "#4caf82", "negativo": "#e57373", "neutral": "#f0c040", "mixto": "#c084fc"}
    bars    = axes[0].bar(conteo.index, conteo.values,
                          color=[colores.get(s, "#aaa") for s in conteo.index],
                          edgecolor="#0e1117", linewidth=1.5)
    axes[0].set_title("Distribución de Sentimientos")
    axes[0].set_ylabel("Comentarios")
    for bar, val in zip(bars, conteo.values):
        axes[0].text(bar.get_x() + bar.get_width() / 2, val + 0.05, str(val),
                     ha="center", color="white", fontweight="bold")

    # Gráfico 2: Scores de afinidad
    x = range(len(df))
    axes[1].plot(x, df["afinidad_positiva"], "o-", color="#4caf82", label="Positiva", linewidth=2)
    axes[1].plot(x, df["afinidad_negativa"], "s-", color="#e57373", label="Negativa", linewidth=2)
    axes[1].set_title("Scores de Afinidad por Comentario")
    axes[1].set_xlabel("Índice del comentario")
    axes[1].set_ylabel("Score (0 – 1)")
    axes[1].set_ylim(0, 1.05)
    axes[1].legend(facecolor="#1a1f2e", labelcolor="white")
    axes[1].grid(True, alpha=0.2, color="#444")

    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # Exportar resultados
    st.subheader("Exportar resultados")
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Resultados NLP")
    st.download_button(
        label="Descargar resultados_nlp.xlsx",
        data=output.getvalue(),
        file_name="resultados_nlp.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# ==============================================================================
# 4. MODULO DE INTEGRACION CON STEAM (CONEXION REAL)
# ==============================================================================
# Aqui es donde demostramos la capacidad de procesar reseñas en tiempo real.

with tab_steam:
    st.subheader("Reseñas reales de Steam")
    st.markdown("Busca cualquier juego y descarga sus reseñas directamente desde Steam para analizarlas.")

    # Buscador
    col_search, col_btn = st.columns([4, 1])
    with col_search:
        nombre_juego = st.text_input("Nombre del juego", placeholder="Ej. Elden Ring, Hades, Cyberpunk 2077...")
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        buscar = st.button("Buscar", type="primary", key="btn_buscar_juego")

    if buscar and nombre_juego.strip():
        with st.spinner(f"Buscando '{nombre_juego}' en Steam..."):
            try:
                juegos = buscar_juego(nombre_juego.strip())
                st.session_state["juegos_encontrados"] = juegos
            except Exception as e:
                st.error(f"❌ Error al conectar con Steam: {e}")

    # ── Selector de juego ─────────────────────
    if "juegos_encontrados" in st.session_state:
        juegos = st.session_state["juegos_encontrados"]

        if not juegos:
            st.warning("No se encontraron juegos con ese nombre. Intenta con otro término.")
        else:
            opciones = {f"{j['name']} (AppID: {j['appid']})": j for j in juegos}
            seleccion = st.radio("Juegos encontrados — selecciona uno:", list(opciones.keys()))
            juego_sel = opciones[seleccion]

            st.divider()

            # ── Opciones de descarga ──────────
            col_cant, col_idioma = st.columns(2)
            with col_cant:
                cantidad = st.slider("¿Cuántas reseñas descargar?", 10, 200, 50, step=10)
            with col_idioma:
                idioma_label = st.selectbox("Idioma de las reseñas", ["Español", "Inglés", "Todos los idiomas"])
                idioma_map = {"Español": "spanish", "Inglés": "english", "Todos los idiomas": "all"}
                idioma = idioma_map[idioma_label]

            st.info(f"Nota: Se analizarán hasta {cantidad} reseñas de {juego_sel['name']} - esto consumirá transacciones de tu cuota Azure.")

            if st.button("Descargar y analizar reseñas", type="primary", key="btn_analizar_steam"):
                # Descargar reseñas
                with st.spinner(f"Descargando {cantidad} reseñas de Steam..."):
                    try:
                        df_steam = obtener_reseñas(
                            appid=juego_sel["appid"],
                            nombre_juego=juego_sel["name"],
                            cantidad=cantidad,
                            idioma=idioma,
                        )
                    except Exception as e:
                        st.error(f"Error al descargar reseñas: {e}")
                        df_steam = None

                if df_steam is not None and len(df_steam) == 0:
                    st.warning("Steam no devolvió reseñas para este juego en el idioma seleccionado. Prueba con 'Todos los idiomas'.")
                if df_steam is not None:
                    st.success(f"OK: {len(df_steam)} reseñas descargadas")

                    # Analizar con Azure
                    df_resultado = procesar_df(df_steam)

                    if df_resultado is not None:
                    # Mostrar resultados completos
                        mostrar_resultados(df_resultado)


# ─────────────────────────────────────────────
# ─────────────────────────────────────────────

with tab_upload:
    st.subheader("Cargar archivo de comentarios")
    st.markdown("El Excel debe tener las columnas: id, juego, usuario, comentario")

    col_up, col_sample = st.columns([3, 1])

    with col_sample:
        # Botón para descargar el Excel de muestra
        ROOT = Path(__file__).parent.parent
        sample_path = ROOT / "data" / "comentarios_steam.xlsx"

        if sample_path.exists():
            with open(sample_path, "rb") as f:
                st.download_button(
                    "Descargar Excel de muestra",
                    data=f.read(),
                    file_name="comentarios_steam.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
        else:
            st.info("Ejecuta `genera_datos.py` para generar el Excel de muestra.")

    with col_up:
        archivo = st.file_uploader("Sube tu archivo Excel", type=["xlsx"])

    if archivo:
        try:
            df_cargado = pd.read_excel(archivo)
            st.success(f"OK: {len(df_cargado)} comentarios cargados")
            st.dataframe(df_cargado, use_container_width=True)

            if st.button("Analizar comentarios", type="primary", key="btn_upload"):
                df_resultado = procesar_df(df_cargado)
                if df_resultado is not None:
                    st.success("OK: Analisis completado. Ve a la pestaña Resultados.")
                    mostrar_resultados(df_resultado)

        except Exception as e:
            st.error(f"❌ Error al leer el archivo: {e}")


# ─────────────────────────────────────────────
# TAB 2 — COMENTARIO MANUAL
# ─────────────────────────────────────────────

with tab_manual:
    st.subheader("Analizar un comentario individual")

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        juego   = st.text_input("Juego", placeholder="Ej. Elden Ring")
        usuario = st.text_input("Usuario", placeholder="Ej. DragonSlayer99")
    with col_f2:
        comentario = st.text_area("Comentario", height=120,
                                  placeholder="Escribe el comentario a analizar...")

    if st.button("Analizar", type="primary", key="btn_manual"):
        if not comentario.strip():
            st.warning("ADVERTENCIA: Escribe un comentario primero.")
        else:
            df_manual = pd.DataFrame([{
                "id": 1,
                "juego": juego or "—",
                "usuario": usuario or "—",
                "comentario": comentario.strip(),
            }])
            df_resultado = procesar_df(df_manual)
            if df_resultado is not None:
                fila = df_resultado.iloc[0]
                st.divider()

                c1, c2, c3 = st.columns(3)
                c1.markdown("**Sentimiento**")
                c1.markdown(badge_sentimiento(fila["sentimiento"]), unsafe_allow_html=True)
                c2.metric("Afinidad positiva", f"{fila['afinidad_positiva']:.0%}")
                c3.metric("Afinidad negativa", f"{fila['afinidad_negativa']:.0%}")

                st.markdown("**Etiquetas extraídas:**")
                st.markdown(tags_html(fila["etiquetas"]), unsafe_allow_html=True)


# ─────────────────────────────────────────────
# TAB 3 — RESULTADOS GUARDADOS
# ─────────────────────────────────────────────

with tab_resultados:
    if "df_resultados" in st.session_state:
        mostrar_resultados(st.session_state["df_resultados"])
    else:
        st.info("Aquí aparecerán los resultados después de analizar un Excel en la pestaña **📂 Cargar Excel**.")
