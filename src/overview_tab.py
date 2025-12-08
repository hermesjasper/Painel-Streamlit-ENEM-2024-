
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from .filters import GlobalFilters


def render_overview_tab(
    stats_df: pd.DataFrame,
    hist_df: pd.DataFrame,
    filters: GlobalFilters,
) -> None:
    stats_filtered = _filter_stats(stats_df, filters)
    hist_filtered = _filter_hist(hist_df, filters)

    if stats_filtered.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
        return

    metric_col = filters.metric_column
    metric_label = filters.disciplina_label

    st.markdown("### Indicadores gerais")
    _render_kpi_row(stats_filtered, metric_col)

    # --- Gráficos lado a lado, cada um com título próprio ---
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### Distribuição das notas")
        st.markdown(
            "<p style='font-size:0.85rem; color:var(--muted-text-color); "
            "margin-top:-0.4rem; margin-bottom:0.75rem;'>"
            "Mostra a proporção de estudantes em cada faixa de pontuação da métrica selecionada."
            "</p>",
            unsafe_allow_html=True,
        )
        _render_distribution_chart_from_hist(hist_filtered, metric_label)

    with col_right:
        st.markdown("#### Participação por tipo de escola")
        st.markdown(
            "<p style='font-size:0.85rem; color:var(--muted-text-color); "
            "margin-top:-0.4rem; margin-bottom:0.75rem;'>"
            "Indica a porcentagem de participantes de cada rede de ensino "
            "(federal, estadual, municipal e privada) para os filtros atuais."
            "</p>",
            unsafe_allow_html=True,
        )
        _render_participation_by_school_type(stats_filtered)



def _filter_stats(stats_df: pd.DataFrame, filters: GlobalFilters) -> pd.DataFrame:
    df = stats_df.copy()

    if filters.redes is not None and "TIPO_ESCOLA" in df.columns:
        df = df[df["TIPO_ESCOLA"].isin(filters.redes)]

    if filters.localizacoes is not None and "LOCALIZACAO" in df.columns:
        df = df[df["LOCALIZACAO"].isin(filters.localizacoes)]

    if filters.ufs is not None and "SG_UF_ESC" in df.columns:
        df = df[df["SG_UF_ESC"].isin(filters.ufs)]

    return df


def _filter_hist(hist_df: pd.DataFrame, filters: GlobalFilters) -> pd.DataFrame:
    df = hist_df.copy()

    if filters.redes is not None and "TIPO_ESCOLA" in df.columns:
        df = df[df["TIPO_ESCOLA"].isin(filters.redes)]

    if filters.localizacoes is not None and "LOCALIZACAO" in df.columns:
        df = df[df["LOCALIZACAO"].isin(filters.localizacoes)]

    if filters.ufs is not None and "SG_UF_ESC" in df.columns:
        df = df[df["SG_UF_ESC"].isin(filters.ufs)]

    if "metric" in df.columns:
        df = df[df["metric"] == filters.metric_column]

    return df


def _render_kpi_row(stats_df: pd.DataFrame, metric_col: str) -> None:
    sum_col = f"sum_{metric_col}"
    if sum_col not in stats_df.columns:
        st.warning("Coluna agregada não encontrada para a métrica selecionada.")
        return

    total_n = stats_df["n"].sum()
    total_sum = stats_df[sum_col].sum()
    mean_metric = total_sum / total_n if total_n > 0 else np.nan

    public_types = {"Federal", "Estadual", "Municipal"}
    private_types = {"Privada"}

    mean_public = np.nan
    mean_private = np.nan
    pct_private = np.nan

    if "TIPO_ESCOLA" in stats_df.columns:
        public_mask = stats_df["TIPO_ESCOLA"].isin(public_types)
        private_mask = stats_df["TIPO_ESCOLA"].isin(private_types)

        if public_mask.any():
            n_pub = stats_df.loc[public_mask, "n"].sum()
            s_pub = stats_df.loc[public_mask, sum_col].sum()
            if n_pub > 0:
                mean_public = s_pub / n_pub

        if private_mask.any():
            n_priv = stats_df.loc[private_mask, "n"].sum()
            s_priv = stats_df.loc[private_mask, sum_col].sum()
            if n_priv > 0:
                mean_private = s_priv / n_priv

            pct_private = n_priv / total_n * 100 if total_n > 0 else np.nan

    diff_public_private = (
        float("nan") if np.isnan(mean_public) or np.isnan(mean_private) else mean_public - mean_private
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Nota média", f"{mean_metric:.1f}")

    with col2:
        st.metric("Número de participantes", f"{int(total_n):,}".replace(",", "."))

    with col3:
        st.metric(
            "Diferença (Pública - Privada)",
            "n/d" if np.isnan(diff_public_private) else f"{diff_public_private:.1f}",
        )

    with col4:
        st.metric(
            "% participantes da rede privada",
            "n/d" if np.isnan(pct_private) else f"{pct_private:.1f} %",
        )


def _render_distribution_chart_from_hist(hist_df: pd.DataFrame, metric_label: str) -> None:
    if hist_df.empty:
        st.info("Sem dados suficientes para o histograma com os filtros atuais.")
        return

    grouped = (
        hist_df.groupby(["bin_idx", "bin_left", "bin_right"])["count"]
        .sum()
        .reset_index()
    )

    total = grouped["count"].sum()
    grouped["density"] = grouped["count"] / total if total > 0 else 0

    grouped["bin_center"] = (grouped["bin_left"] + grouped["bin_right"]) / 2

    fig = px.bar(
        grouped,
        x="bin_center",
        y="density",
        labels={
            "bin_center": metric_label,
            "density": "Proporção de estudantes",
        },
    )
    fig.update_layout(
        bargap=0.05,
        margin=dict(l=10, r=10, t=10, b=40),
        template="simple_white",
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_participation_by_school_type(stats_df: pd.DataFrame) -> None:
    if "TIPO_ESCOLA" not in stats_df.columns:
        st.info("Informações sobre o tipo de escola não estão disponíveis.")
        return

    counts = (
        stats_df.groupby("TIPO_ESCOLA")["n"]
        .sum()
        .rename("n")
        .reset_index()
    )
    total = counts["n"].sum()
    counts["percentual"] = counts["n"] / total * 100 if total > 0 else 0

    fig = px.bar(
        counts,
        x="TIPO_ESCOLA",
        y="percentual",
        text="percentual",
        labels={"percentual": "% de participantes", "TIPO_ESCOLA": "Tipo de escola"},
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(
        yaxis=dict(range=[0, counts["percentual"].max() * 1.25]),
        margin=dict(l=10, r=10, t=10, b=40),
        template="simple_white",
    )
    st.plotly_chart(fig, use_container_width=True)
