from __future__ import annotations

from pathlib import Path
from typing import Optional, List

import json

import pandas as pd
import plotly.express as px
import streamlit as st

from .filters import GlobalFilters
from .config import THEME
import plotly.graph_objects as go


def format_decimal_br(value: float, decimals: int = 1) -> str:
    """Formata número no padrão brasileiro: milhar com ponto, decimal com vírgula."""
    if value is None or pd.isna(value):
        return "-"
    s = f"{value:,.{decimals}f}"  # 1,234.5
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return s


def _apply_map_filters(df: pd.DataFrame, filters: GlobalFilters) -> pd.DataFrame:
    out = df.copy()

    if filters.redes is not None and len(filters.redes) > 0:
        out = out[out["TIPO_ESCOLA"].isin(filters.redes)]

    if filters.localizacoes is not None and len(filters.localizacoes) > 0:
        out = out[out["LOCALIZACAO"].isin(filters.localizacoes)]

    if filters.ufs is not None and len(filters.ufs) > 0:
        out = out[out["SG_UF_ESC"].isin(filters.ufs)]

    return out


def _build_uf_summary(df: pd.DataFrame, metric_col: str) -> pd.DataFrame:
    """
    A partir da tabela agregada (por UF/rede/localização), gera um resumo por UF:
    - n_participantes
    - soma da métrica
    - nota média da métrica
    """
    metric_sum_col = f"sum_{metric_col}"
    if metric_sum_col not in df.columns:
        raise KeyError(
            f"Coluna '{metric_sum_col}' não encontrada na base agregada. "
            "Verifique o script de pré-processamento."
        )

    uf_summary = (
        df.groupby("SG_UF_ESC", as_index=False)
        .agg(
            n_participantes=("n_participantes", "sum"),
            sum_metric=(metric_sum_col, "sum"),
        )
        .query("n_participantes > 0")
    )

    uf_summary["nota_media"] = uf_summary["sum_metric"] / uf_summary["n_participantes"]
    return uf_summary


def render_map_tab(map_df: pd.DataFrame, filters: GlobalFilters) -> None:
    """
    Renderiza a aba 'Mapa & Território'.

    Espera receber a tabela agregada (data/enem_map_uf.parquet)
    e os filtros globais (rede, localização, UF, disciplina/métrica).
    """
    df_filtered = _apply_map_filters(map_df, filters)

    if df_filtered.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
        return

    metric_col = filters.metric_column
    metric_label = filters.disciplina_label

    uf_summary = _build_uf_summary(df_filtered, metric_col)

    if uf_summary.empty:
        st.warning("Nenhum dado agregado por UF para os filtros selecionados.")
        return

    # ---------------- KPIs principais ----------------
    total_participantes = uf_summary["n_participantes"].sum()
    nota_media_brasil = (
    (uf_summary["nota_media"] * uf_summary["n_participantes"]).sum()
    / total_participantes
    )

    uf_max = uf_summary.loc[uf_summary["nota_media"].idxmax()]
    uf_min = uf_summary.loc[uf_summary["nota_media"].idxmin()]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            f"Nota média ({metric_label}) - Brasil",
            format_decimal_br(nota_media_brasil, 1),
        )

    with col2:
        st.metric(
            f"Maior nota média ({metric_label})",
            f"{uf_max['SG_UF_ESC']} – {format_decimal_br(uf_max['nota_media'], 1)}",
        )

    with col3:
        st.metric(
            f"Menor nota média ({metric_label})",
            f"{uf_min['SG_UF_ESC']} – {format_decimal_br(uf_min['nota_media'], 1)}",
        )

    st.markdown("<div style='height:0.75rem;'></div>", unsafe_allow_html=True)

    # ---------------- Mapa + ranking ----------------
    col_map, col_rank = st.columns([2, 1])

    with col_map:
        st.markdown("#### Mapa de notas por UF")
        st.markdown(
            "<p style='font-size:0.85rem; color:var(--muted-text-color); "
            "margin-top:-0.35rem; margin-bottom:0.75rem;'>"
            "Cada estado é colorido pela nota média da métrica selecionada, "
            "após aplicação dos filtros de rede, localização e UF."
            "</p>",
            unsafe_allow_html=True,
        )

        geo_path = Path("data/br_states.geojson")
        if not geo_path.exists():
            st.info(
                "Para visualizar o mapa, adicione o arquivo "
                "`data/br_states.geojson` com os polígonos das UFs "
                "(precisa ter uma propriedade `sigla` com AC, AL, ...). "
                "Enquanto isso, veja o ranking ao lado."
            )
        else:
            with geo_path.open(encoding="utf-8") as f:
                geojson = json.load(f)

            fig = px.choropleth(
                uf_summary,
                geojson=geojson,
                locations="SG_UF_ESC",
                featureidkey="id",  # ajuste se sua geojson usar outro nome
                color="nota_media",
                color_continuous_scale="Blues",
                labels={"nota_media": f"Nota média ({metric_label})"},
            )

            fig.update_geos(
                fitbounds="locations",
                visible=False,
                bgcolor="rgba(0,0,0,0)",
            )

            fig.update_layout(
                margin=dict(l=0, r=0, t=0, b=0),
                coloraxis_colorbar=dict(
                    title=f"Nota média<br>({metric_label})",
                    ticksuffix="",
                ),
                font=dict(color="#e5e7eb"),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )

            st.plotly_chart(fig, use_container_width=True)

    with col_rank:
        st.markdown("#### Ranking por UF")
        st.markdown(
            "<p style='font-size:0.85rem; color:var(--muted-text-color); "
            "margin-top:-0.35rem; margin-bottom:0.75rem;'>"
            "Lista ordenada dos estados pela nota média da métrica selecionada."
            "</p>",
            unsafe_allow_html=True,
        )

        rank_df = uf_summary.copy()
        rank_df = rank_df.sort_values("nota_media", ascending=False)

        # Formatação brasileira
        rank_df["Nota média"] = rank_df["nota_media"].apply(
            lambda v: format_decimal_br(v, 1)
        )
        rank_df["Participantes"] = rank_df["n_participantes"].apply(
            lambda v: f"{int(v):,}".replace(",", ".")
        )

        tabela = (
            rank_df[["SG_UF_ESC", "Nota média", "Participantes"]]
            .rename(columns={"SG_UF_ESC": "UF"})
            .reset_index(drop=True)
        )

        # Tabela Plotly em tema escuro
        fig_table = go.Figure(
            data=[
                go.Table(
                    header=dict(
                        values=list(tabela.columns),
                        fill_color="#020617",  # fundo bem escuro
                        align="left",
                        font=dict(color="#f9fafb", size=12, family="system-ui"),
                        line_color="rgba(15,23,42,0.9)",
                    ),
                    cells=dict(
                        values=[tabela[col] for col in tabela.columns],
                        fill_color="#020617",
                        align="left",
                        font=dict(color="#e5e7eb", size=11, family="system-ui"),
                        line_color="rgba(30,64,175,0.4)",
                        height=26,
                    ),
                )
            ]
        )

        fig_table.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=420,
        )

        st.plotly_chart(fig_table, use_container_width=True)

