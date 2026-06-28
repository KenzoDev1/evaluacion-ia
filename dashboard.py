"""
Dashboard de Observabilidad — dashboard_skill
Lee los registros reales de logs/execution_logs.jsonl y presenta
KPIs, gráficos de latencia, distribución de riesgos y estado de herramientas.
Ejecutar con: streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
import json
import os
import plotly.express as px
from datetime import datetime

# ── Configuración de Página ────────────────────────────────────────
st.set_page_config(
    page_title="Observabilidad - Auditor AquaChile",
    page_icon="📊",
    layout="wide",
)

LOG_FILE = "logs/execution_logs.jsonl"
REFRESH_INTERVAL = 30  # segundos


# ── Carga de Datos Reales ──────────────────────────────────────────
@st.cache_data(ttl=REFRESH_INTERVAL)
def load_execution_logs() -> pd.DataFrame:
    """Lee y parsea el archivo JSONL de logs reales. Nunca usa datos simulados."""
    if not os.path.exists(LOG_FILE):
        return pd.DataFrame()
    records = []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped:
                records.append(json.loads(stripped))
    if not records:
        return pd.DataFrame()
    return pd.DataFrame(records)


# ── Encabezado ─────────────────────────────────────────────────────
st.title("📊 Dashboard de Observabilidad — Auditor de Riesgos AquaChile")
st.caption("Datos extraídos en tiempo real desde `logs/execution_logs.jsonl`")

df = load_execution_logs()

if df.empty:
    st.warning(
        "⚠️ No hay datos de ejecución registrados aún. "
        "Ejecuta el agente con `python3 app.py` para generar logs de observabilidad."
    )
    st.stop()

# ── KPIs Principales ──────────────────────────────────────────────
st.markdown("### Métricas Generales")
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

with kpi1:
    st.metric(label="Total Ejecuciones", value=len(df))
with kpi2:
    st.metric(label="Tokens Consumidos", value=f"{int(df['total_tokens'].sum()):,}")
with kpi3:
    avg_latency = round(df["total_latency_ms"].mean(), 1)
    st.metric(label="Latencia Promedio", value=f"{avg_latency} ms")
with kpi4:
    avg_cpu = round(df["cpu_percent_end"].mean(), 1)
    st.metric(label="CPU Promedio (%)", value=f"{avg_cpu}%")
with kpi5:
    avg_ram = round(df["ram_percent_end"].mean(), 1)
    st.metric(label="RAM Promedio (%)", value=f"{avg_ram}%")

st.markdown("---")

# ── Gráficos Principales ──────────────────────────────────────────
col_left, col_right = st.columns(2)

# Gráfico 1: Latencia promedio por herramienta (barras)
with col_left:
    st.subheader("⏱️ Latencia Promedio por Herramienta")
    tool_latency_rows = []
    for _, row in df.iterrows():
        latencies = row.get("tool_latencies_ms")
        if isinstance(latencies, dict):
            for tool_name, latency_val in latencies.items():
                tool_latency_rows.append(
                    {"Herramienta": tool_name, "Latencia (ms)": latency_val}
                )

    if tool_latency_rows:
        df_lat = pd.DataFrame(tool_latency_rows)
        avg_by_tool = (
            df_lat.groupby("Herramienta")["Latencia (ms)"]
            .mean()
            .reset_index()
            .sort_values("Latencia (ms)", ascending=False)
        )
        fig_lat = px.bar(
            avg_by_tool,
            x="Herramienta",
            y="Latencia (ms)",
            color="Herramienta",
            title="Latencia promedio por herramienta (ms)",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig_lat.update_layout(showlegend=False)
        st.plotly_chart(fig_lat, use_container_width=True)
    else:
        st.info("No hay datos de latencia de herramientas registrados.")

# Gráfico 2: Distribución de clasificaciones de riesgo (torta)
with col_right:
    st.subheader("🎯 Distribución de Clasificaciones de Riesgo")
    risk_counts = df["risk_classification"].value_counts().reset_index()
    risk_counts.columns = ["Nivel de Riesgo", "Cantidad"]

    color_map = {"Alto": "#e74c3c", "Medio": "#f39c12", "Bajo": "#2ecc71", "No evaluado": "#95a5a6"}
    fig_risk = px.pie(
        risk_counts,
        names="Nivel de Riesgo",
        values="Cantidad",
        title="Proporción de riesgos emitidos (Alto / Medio / Bajo)",
        hole=0.45,
        color="Nivel de Riesgo",
        color_discrete_map=color_map,
    )
    st.plotly_chart(fig_risk, use_container_width=True)

st.markdown("---")

# ── Gráfico 3: Tasa de éxito/fallo por herramienta ────────────────
st.subheader("📈 Tasa de Éxito / Fallo por Herramienta")
tool_status_rows = []
for _, row in df.iterrows():
    statuses = row.get("tool_status")
    if isinstance(statuses, dict):
        for tool_name, status_val in statuses.items():
            tool_status_rows.append(
                {"Herramienta": tool_name, "Estado": status_val}
            )

if tool_status_rows:
    df_status = pd.DataFrame(tool_status_rows)
    status_agg = (
        df_status.groupby(["Herramienta", "Estado"])
        .size()
        .reset_index(name="Cantidad")
    )
    fig_status = px.bar(
        status_agg,
        x="Herramienta",
        y="Cantidad",
        color="Estado",
        barmode="stack",
        title="Ejecuciones exitosas vs. fallidas por herramienta",
        color_discrete_map={"success": "#2ecc71", "error": "#e74c3c"},
    )
    st.plotly_chart(fig_status, use_container_width=True)
else:
    st.info("No hay datos de estado de herramientas registrados.")

st.markdown("---")

# ── Tabla: Últimos 10 Registros ────────────────────────────────────
st.subheader("📋 Últimos 10 Registros de Ejecución")

display_df = df.copy()
display_df = display_df.sort_values(by="timestamp", ascending=False).head(10)

columns_to_show = [
    "execution_id",
    "timestamp",
    "total_latency_ms",
    "total_tokens",
    "risk_classification",
    "cpu_percent_end",
    "ram_percent_end",
]
available_cols = [c for c in columns_to_show if c in display_df.columns]
st.dataframe(display_df[available_cols], use_container_width=True, hide_index=True)

# ── Auto-refresh ───────────────────────────────────────────────────
st.caption(f"Los datos se actualizan automáticamente cada {REFRESH_INTERVAL} segundos.")
