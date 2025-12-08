from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from .filters import GlobalFilters, apply_filters


def render_schools_tab(schools_df: pd.DataFrame, filters: GlobalFilters) -> None:
    """
    Aba "Escolas & Desigualdades".

    Usa a tabela agregada por escola (schools_stats.parquet), onde cada linha representa uma escola com:
      - school_id,
      - TIPO_ESCOLA, LOCALIZACAO, SG_UF_ESC,
      - n_participantes,
      - media_<métrica> (ex.: media_nota_final, media_NU_NOTA_CN, ...).

    A métrica exibida é controlada pelo seletor global de disciplina/métrica.
    """

    # 1) Qual coluna de média usar, com base na métrica selecionada
    base_metric = filters.metric_column          # ex.: "nota_final"
    metric_col = f"media_{base_metric}"          # ex.: "media_nota_final"

    if metric_col not in schools_df.columns:
        metric_col = "media_nota_final"

    # 2) Aplica filtros globais (rede, localização, UF)
    df = apply_filters(schools_df, filters).copy()
    df = df.dropna(subset=[metric_col]).copy()

    if df.empty:
        st.info("Nenhuma escola encontrada com os filtros atuais.")
        return

    # ------------------ KPIs de desigualdade ------------------

    n_schools = len(df)
    mean_metric = df[metric_col].mean()

    df_sorted = df.sort_values(metric_col)
    k = max(1, int(0.1 * n_schools))
    bottom_mean = df_sorted.head(k)[metric_col].mean()
    top_mean = df_sorted.tail(k)[metric_col].mean()
    gap = top_mean - bottom_mean

    def fmt_num(v: float, casas: int = 1) -> str:
        return f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric(
            "Nº de escolas (filtros atuais)",
            f"{n_schools:,}".replace(",", "."),
        )
    with c2:
        st.metric(
            f"Média das escolas ({_metric_label_pt(base_metric)})",
            fmt_num(mean_metric),
        )
    with c3:
        st.metric(
            "Média Top 10% escolas",
            fmt_num(top_mean),
        )
    with c4:
        st.metric(
            "Gap Top 10% vs Bottom 10%",
            fmt_num(gap),
        )

    st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)

    # ------------------------------------------------------------------
    # 1º BLOCO VISUAL: HISTOGRAMAS EMPILHADOS (UM POR REDE) – BARRAS VERTICAIS
    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # 1º BLOCO VISUAL: HISTOGRAMAS EMPILHADOS (UM POR REDE) – BARRAS VERTICAIS
    # ------------------------------------------------------------------

    st.markdown(
        "### Distribuição das médias por rede de ensino\n"
        f"({_metric_label_pt(base_metric)})"
    )

    if "TIPO_ESCOLA" in df.columns:
        redes = sorted(df["TIPO_ESCOLA"].dropna().unique().tolist())

        # Bins globais (para todas as redes) – mais bins = mais barras
        global_min = float(df[metric_col].min())
        global_max = float(df[metric_col].max())
        if global_min == global_max:
            global_min -= 1.0
            global_max += 1.0

        nbins = 20  # <- aumente/diminua se quiser mais/menos barras
        bin_edges = np.linspace(global_min, global_max, nbins + 1)
        bin_widths = np.diff(bin_edges)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

        for rede in redes:
            sub = df[df["TIPO_ESCOLA"] == rede].copy()
            if sub.empty:
                continue

            st.markdown(f"##### {rede}")

            vals = sub[metric_col].dropna().values
            counts, _ = np.histogram(vals, bins=bin_edges)

            # Mantém só bins com pelo menos 1 escola
            mask = counts > 0
            if not mask.any():
                st.info("Nenhuma escola nessa faixa de notas para esta rede.")
                continue

            counts_plot = counts[mask]
            centers_plot = bin_centers[mask]
            widths_plot = bin_widths[mask]

            # Texto do hover com faixa de média formatada
            hovertext = []
            idxs = np.where(mask)[0]
            for i, c in zip(idxs, counts_plot):
                left = bin_edges[i]
                right = bin_edges[i + 1]
                left_txt = f"{left:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
                right_txt = f"{right:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
                hovertext.append(
                    f"Faixa de média: {left_txt} – {right_txt}<br>"
                    f"Nº de escolas: {c}"
                )

            fig_hist = go.Figure(
                data=[
                    go.Bar(
                        x=centers_plot,           # eixo X numérico (centro dos bins)
                        y=counts_plot,            # nº de escolas
                        width=widths_plot,        # largura = tamanho do bin
                        marker_line_width=0,      # sem borda
                        text=None,
                        hovertext=hovertext,
                        hovertemplate="%{hovertext}<extra></extra>",
                    )
                ]
            )

            fig_hist.update_xaxes(
                title_text=f"Média {_metric_label_pt(base_metric)}",
                tickformat=".0f",
            )
            fig_hist.update_yaxes(
                title_text="Nº de escolas",
            )

            fig_hist.update_layout(
                height=200,  # um pouco maior porque agora há mais barras
                margin=dict(l=10, r=10, t=5, b=40),
                showlegend=False,
                bargap=0,          # <- sem espaço entre barras
                bargroupgap=0,
                hoverlabel=dict(
                    bgcolor="#020617",   # fundo escuro no hover
                    font_color="#f9fafb"
                ),
            )

            st.plotly_chart(fig_hist, use_container_width=True)
    else:
        st.info("Coluna 'TIPO_ESCOLA' não encontrada na base agregada de escolas.")

    st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)


    # ------------------------------------------------------------------
    # 2º BLOCO VISUAL: RANKING DE ESCOLAS
    # ------------------------------------------------------------------

    st.markdown(
        "### Ranking de escolas por média\n"
        f"({_metric_label_pt(base_metric)})"
    )

    top_n = 20
    df_rank = df.sort_values(metric_col, ascending=False).head(top_n).copy()

    # Rótulo: ID + UF (não temos nome)
    if "school_id" in df_rank.columns and "SG_UF_ESC" in df_rank.columns:
        df_rank["label_escola"] = (
            df_rank["school_id"].astype(str)
            + " (" + df_rank["SG_UF_ESC"].astype(str) + ")"
        )
        y_col = "label_escola"
        y_title = "Escola (ID + UF)"
    else:
        df_rank["label_escola"] = df_rank.index.astype(str)
        y_col = "label_escola"
        y_title = "Escola"

    df_rank_sorted = df_rank.sort_values(metric_col, ascending=True)

    fig_rank = go.Figure(
        data=[
            go.Bar(
                x=df_rank_sorted[metric_col],
                y=df_rank_sorted[y_col],
                orientation="h",
                hovertemplate=(
                    "Escola: %{y}<br>"
                    "Média "
                    + _metric_label_pt(base_metric)
                    + ": %{x:.2f}<extra></extra>"
                ),
            )
        ]
    )

    fig_rank.update_xaxes(
        title_text=f"Média {_metric_label_pt(base_metric)}",
    )
    fig_rank.update_yaxes(
        title_text=y_title,
    )

    fig_rank.update_layout(
        height=550,
        margin=dict(l=10, r=10, t=10, b=10),
        hoverlabel=dict(
            bgcolor="#020617",
            font_color="#f9fafb",
        ),
    )

    st.plotly_chart(fig_rank, use_container_width=True)


def _metric_label_pt(base_metric: str) -> str:
    """
    Converte o nome da coluna base (ex.: 'nota_final', 'NU_NOTA_MT')
    em um rótulo amigável em português.
    """
    mapping = {
        "nota_final": "nota final",
        "NU_NOTA_CN": "Ciências da Natureza",
        "NU_NOTA_CH": "Ciências Humanas",
        "NU_NOTA_LC": "Linguagens e Códigos",
        "NU_NOTA_MT": "Matemática",
        "NU_NOTA_REDACAO": "Redação",
    }
    return mapping.get(base_metric, base_metric)
