from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


# ------------------------------
# Helpers de formatação (pt-BR)
# ------------------------------


def _fmt_num(x: Optional[float], dec: int = 1) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "-"
    return f"{x:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_pct(x: Optional[float], dec: int = 1) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "-"
    return f"{x*100:,.{dec}f}%".replace(",", "X").replace(".", ",").replace("X", ".")


# ------------------------------
# Aba IDEB
# ------------------------------


def render_ideb_tab(ideb_df: pd.DataFrame) -> None:
    """
    Aba 'Linha do Tempo IDEB':

    - KPIs:
        * Último IDEB (Pública / Privada)
        * Diferença entre redes no último ano
        * Variação da rede pública desde o primeiro ano

    - Gráfico de linha mostrando a evolução das notas IDEB (EM, Brasil)
      por rede de ensino.
    """

    if ideb_df.empty:
        st.warning("Nenhum dado de IDEB disponível.")
        return

    # Garante tipos corretos
    df = ideb_df.copy()
    df["Ano"] = df["Ano"].astype(str)
    df["IDEB_Score"] = pd.to_numeric(df["IDEB_Score"], errors="coerce")
    df = df.dropna(subset=["IDEB_Score"])

    # Ordena cronologicamente
    anos_ordenados = sorted(df["Ano"].unique(), key=lambda x: int(x))
    df["Ano"] = pd.Categorical(df["Ano"], categories=anos_ordenados, ordered=True)

    # ---------------- KPIs ----------------
    ultimo_ano = anos_ordenados[-1]
    primeiro_ano = anos_ordenados[0]

    df_last = df[df["Ano"] == ultimo_ano]
    df_first = df[df["Ano"] == primeiro_ano]

    # Último IDEB por rede
    pub_last = df_last.loc[df_last["Rede"] == "Pública", "IDEB_Score"].mean()
    priv_last = df_last.loc[df_last["Rede"] == "Privada", "IDEB_Score"].mean()

    # Diferença entre redes no último ano
    diff_last = None
    if not np.isnan(pub_last) and not np.isnan(priv_last):
        diff_last = priv_last - pub_last

    # Variação da rede pública desde o primeiro ano
    pub_first = df_first.loc[df_first["Rede"] == "Pública", "IDEB_Score"].mean()
    delta_pub = None
    if not np.isnan(pub_first) and not np.isnan(pub_last):
        delta_pub = pub_last - pub_first

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("IDEB – rede pública (último ano)", _fmt_num(pub_last, 1))

    with col2:
        st.metric("IDEB – rede privada (último ano)", _fmt_num(priv_last, 1))

    with col3:
        if diff_last is not None:
            sinal = "+" if diff_last >= 0 else "-"
            st.metric(
                f"Vantagem rede privada em {ultimo_ano}",
                _fmt_num(abs(diff_last), 1),
                help="Diferença (privada – pública) no último ano da série.",
            )
        else:
            st.metric(f"Vantagem rede privada em {ultimo_ano}", "-")

    st.markdown("<div style='margin-top:1.25rem;'></div>", unsafe_allow_html=True)

    # Delta da rede pública no rodapé dos KPIs
    if delta_pub is not None:
        texto_delta = (
            f"A rede pública saiu de {_fmt_num(pub_first,1)} em {primeiro_ano} "
            f"para {_fmt_num(pub_last,1)} em {ultimo_ano}, "
            f"um avanço de {_fmt_num(delta_pub,1)} pontos no IDEB."
        )
        st.markdown(
            f"<p style='font-size:0.9rem; color:var(--muted-text-color);'>"
            f"{texto_delta}</p>",
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)

    # ---------------- Gráfico de linha ----------------
    # ---------------- GRÁFICO PRINCIPAL ----------------

    st.markdown(
        "#### Evolução da nota IDEB por rede de ensino (Ensino Médio – Brasil)"
    )

    # faixa de y mais apertada
    y_min = float(df["IDEB_Score"].min())
    y_max = float(df["IDEB_Score"].max())
    padding = 0.3
    y_range = [max(0.0, y_min - padding), y_max + padding]

    fig = px.line(
        df,
        x="Ano",
        y="IDEB_Score",
        color="Rede",
        markers=True,
        labels={
            "Ano": "Ano",
            "IDEB_Score": "Nota IDEB",
            "Rede": "Rede de ensino",
        },
        # cores bem diferentes para pública x privada
        color_discrete_sequence=["#38bdf8", "#f97316"],  # Pública, Privada
    )

    # linhas mais grossas, pontos maiores e hover legível
    fig.update_traces(
        line=dict(width=4),
        marker=dict(size=10, symbol="circle"),
        hovertemplate=(
            "Ano: %{x}<br>"
            "Rede: %{legendgroup}<br>"
            "Nota IDEB: %{y:.1f}<extra></extra>"
        ),
    )

    # grade suave e fundo mais claro atrás das linhas para dar contraste
    fig.update_yaxes(
        range=y_range,
        gridcolor="rgba(148,163,184,0.25)",
        zerolinecolor="rgba(148,163,184,0.35)",
    )
    fig.update_xaxes(
        gridcolor="rgba(31,41,55,0.5)",
        zerolinecolor="rgba(148,163,184,0.35)",
    )

    fig.update_layout(
        height=420,
        margin=dict(l=50, r=40, t=40, b=50),
        # camada de fundo do gráfico um pouco mais clara que o resto da página
        plot_bgcolor="rgba(15,23,42,0.95)",
        paper_bgcolor="rgba(15,23,42,0.0)",
        hoverlabel=dict(
            bgcolor="#020617",
            font_color="#f9fafb",
        ),
        # legenda mais clara e com título
        legend=dict(
            title="Rede de ensino",
            orientation="h",
            yanchor="bottom",
            y=1.08,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(15,23,42,0.9)",
            bordercolor="rgba(148,163,184,0.4)",
            borderwidth=1,
            font=dict(size=11),
        ),
    )

    st.plotly_chart(fig, use_container_width=True)
