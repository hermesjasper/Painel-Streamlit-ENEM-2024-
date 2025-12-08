from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from .filters import GlobalFilters, apply_filters


# ------------------------------
# Helpers de formatação (pt-BR)
# ------------------------------


def _fmt_num(x: Optional[float], dec: int = 1) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "-"
    return f"{x:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_int(n: Optional[float]) -> str:
    if n is None or (isinstance(n, float) and np.isnan(n)):
        return "-"
    return f"{int(n):,}".replace(",", ".")


def _fmt_pct(x: Optional[float], dec: int = 1) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "-"
    return f"{x*100:,.{dec}f}%".replace(",", "X").replace(".", ",").replace("X", ".")


# ------------------------------
# Aba de Redação
# ------------------------------


def render_redacao_tab(
    stats_df: pd.DataFrame,
    hist_df: pd.DataFrame,
    filters: GlobalFilters,
) -> None:
    """
    Aba de Redação:

    - KPIs:
        * Média geral de redação
        * Nº de participantes com redação
        * % de provas zeradas
        * % de provas com nota >= 900

    - Histograma geral das notas de redação
    - % de notas 0 por rede de ensino
    """

    # Aplicamos apenas filtros de dimensão (rede, localização, UF).
    # A coluna de métrica é sempre redação (agregada).
    stats_filtered = apply_filters(stats_df, filters)
    hist_filtered = apply_filters(hist_df, filters)

    if stats_filtered.empty:
        st.warning("Nenhum dado de redação para os filtros selecionados.")
        return

    # -----------------------------------
    # KPIs principais da aba Redação
    # -----------------------------------
    total_n = stats_filtered["n"].sum()
    total_sum = stats_filtered["sum_redacao"].sum()
    total_zero = stats_filtered["n_zero"].sum()
    total_900 = stats_filtered["n_900mais"].sum()

    media_redacao = total_sum / total_n if total_n > 0 else np.nan
    pct_zero = total_zero / total_n if total_n > 0 else np.nan
    pct_900 = total_900 / total_n if total_n > 0 else np.nan

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Média de redação", _fmt_num(media_redacao, 1))

    with col2:
        st.metric("Nº de participantes (redação)", _fmt_int(total_n))

    with col3:
        st.metric("% de provas zeradas", _fmt_pct(pct_zero, 1))

    with col4:
        st.metric("% com nota ≥ 900", _fmt_pct(pct_900, 1))

    st.markdown("<div style='margin-top:1.25rem;'></div>", unsafe_allow_html=True)

    # -----------------------------------
    # Histograma geral das notas de redação
    # -----------------------------------
    st.markdown("#### Distribuição das notas de redação")

    hist_grouped = (
        hist_filtered.groupby(["bin_idx", "bin_left", "bin_right"], as_index=False)["count"]
        .sum()
    )

    if hist_grouped.empty:
        st.info("Não há dados suficientes para montar o histograma de redação.")
    else:
        hovertext = []
        for _, row in hist_grouped.iterrows():
            left_txt = f"{row['bin_left']:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
            right_txt = f"{row['bin_right']:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
            hovertext.append(
                f"Faixa de nota: {left_txt} – {right_txt}<br>"
                f"Nº de participantes: {_fmt_int(row['count'])}"
            )

        fig_hist = go.Figure(
            data=[
                go.Bar(
                    x=hist_grouped["bin_left"],
                    y=hist_grouped["count"],
                    width=hist_grouped["bin_right"] - hist_grouped["bin_left"],
                    marker_line_width=0,
                    hovertext=hovertext,
                    hovertemplate="%{hovertext}<extra></extra>",
                )
            ]
        )

        fig_hist.update_xaxes(
            title_text="Nota de redação",
            range=[0, 1000],
        )
        fig_hist.update_yaxes(title_text="Nº de participantes")

        fig_hist.update_layout(
            bargap=0,
            bargroupgap=0,
            margin=dict(l=10, r=10, t=10, b=40),
            hoverlabel=dict(
                bgcolor="#020617",
                font_color="#f9fafb",
            ),
        )

        st.plotly_chart(fig_hist, use_container_width=True)

    st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)

    # -----------------------------------
    # % de notas 0 por rede de ensino
    # -----------------------------------
    if "TIPO_ESCOLA" in stats_filtered.columns:
        st.markdown("#### Percentual de notas 0 por rede de ensino")

        by_rede = (
            stats_filtered.groupby("TIPO_ESCOLA", as_index=False)[["n", "n_zero"]]
            .sum()
        )
        by_rede["pct_zero"] = by_rede["n_zero"] / by_rede["n"]

        fig_zero = px.bar(
            by_rede.sort_values("pct_zero", ascending=False),
            x="TIPO_ESCOLA",
            y="pct_zero",
            labels={
                "TIPO_ESCOLA": "Rede de ensino",
                "pct_zero": "% de provas zeradas",
            },
        )

        fig_zero.update_traces(
            hovertemplate=(
                "Rede: %{x}<br>"
                "% de provas zeradas: %{y:.2%}<extra></extra>"
            )
        )

        fig_zero.update_yaxes(
            tickformat=".0%",
        )
        fig_zero.update_layout(
            margin=dict(l=10, r=10, t=10, b=40),
            hoverlabel=dict(
                bgcolor="#020617",
                font_color="#f9fafb",
            ),
        )

        st.plotly_chart(fig_zero, use_container_width=True)
    else:
        st.info("Coluna 'TIPO_ESCOLA' não encontrada para calcular % de notas 0 por rede.")
