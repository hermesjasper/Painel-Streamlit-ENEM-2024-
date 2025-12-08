from pathlib import Path

import streamlit as st

from src.config import THEME, LOGO_PATH
from src.data_loader import (
    load_overview_stats,
    load_overview_hist,
    load_map_uf_data,
    load_schools_data,
    load_redacao_stats,
    load_redacao_hist,
    load_ideb_brasil_em,    # 👈 novo
)

from src.ideb_tab import render_ideb_tab   # 👈 novo

from src.redacao_tab import render_redacao_tab
from src.schools_tab import render_schools_tab

from src.filters import render_global_filters
from src.overview_tab import render_overview_tab
from src.map_tab import render_map_tab
from src.schools_tab import render_schools_tab  # 🔹 novo
from src.utils import inject_base_css, inject_theme_variables



def main() -> None:
    st.set_page_config(
        page_title="Painel ENEM 2024",
        layout="wide",
        page_icon="📊",
    )

    inject_theme_variables(THEME)
    inject_base_css()

    # Cabeçalho com logo (esquerda) + título centralizado + nomes à direita
    col_logo, col_title, col_right = st.columns([1, 4, 2])

    with col_logo:
        logo_path = Path(LOGO_PATH)
        if logo_path.exists():
            # Sem use_column_width (depreciado)
            st.image(str(logo_path), width=90)

    with col_title:
        st.markdown(
            """
            <div style="display:flex; flex-direction:column;
                        align-items:center; justify-content:center; height:100%;">
                <h1 style="margin:0; text-align:center;">Painel ENEM 2024</h1>
                <p class="header-subtitle" style="margin-top:0.25rem; text-align:center;">
                    Visão geral do desempenho no ENEM 2024 e das desigualdades entre redes de ensino.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_right:
        st.markdown(
            """
            <div style="
                display:flex;
                flex-direction:column;
                justify-content:center;
                align-items:flex-end;
                height:100%;
                text-align:right;
                font-size:0.8rem;
                color:var(--muted-text-color);
                line-height:1.25;
            ">
                <span>Hermes Winarski</span>
                <span>Leonardo Amaral</span>
                <span>Marcelo Cavalcanti</span>
                <span>Matheus Lira</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # pequeno espaçamento abaixo do cabeçalho
    st.markdown("<div style='margin-bottom:0.75rem;'></div>", unsafe_allow_html=True)


    # Carregamento de dados
    # Carregamento de dados
    stats_df = load_overview_stats()
    hist_df = load_overview_hist()
    map_df = load_map_uf_data()
    schools_df = load_schools_data()
    redacao_stats_df = load_redacao_stats()
    redacao_hist_df = load_redacao_hist()
    ideb_df = load_ideb_brasil_em()


    # Tabs
    tab_overview, tab_mapa, tab_escolas, tab_redacao, tab_ideb = st.tabs(
        [
            "Visão Geral",
            "Mapa & Território",
            "Escolas & Desigualdades",
            "Redação",
            "Linha do Tempo IDEB",
        ]
    )

    # Aba Visão Geral
    with tab_overview:
        st.markdown("### Filtros")
        filters_overview = render_global_filters(stats_df, key_prefix="ov_")
        st.markdown("<div style='margin-bottom:0.5rem;'></div>", unsafe_allow_html=True)
        render_overview_tab(stats_df, hist_df, filters_overview)

    # Aba Mapa & Território
    with tab_mapa:
        st.markdown("### Filtros")
        filters_map = render_global_filters(map_df, key_prefix="map_")
        st.markdown("<div style='margin-bottom:0.5rem;'></div>", unsafe_allow_html=True)
        render_map_tab(map_df, filters_map)

    # Outras abas (placeholder)
     # Aba Escolas & Desigualdades
    with tab_escolas:
        st.markdown("### Filtros")
        filters_schools = render_global_filters(schools_df, key_prefix="sch_")
        st.markdown("<div style='margin-bottom:0.5rem;'></div>", unsafe_allow_html=True)
        render_schools_tab(schools_df, filters_schools)

    # Aba Redação
    with tab_redacao:
        st.markdown("### Filtros")
        filters_red = render_global_filters(
            redacao_stats_df,
            key_prefix="red_",
            show_metric=False,              # mantém SEM seletor de métrica, focado em redação
            default_metric_label="Redação", # fixa a métrica como Redação, se isso estiver sendo usado
        )
        st.markdown("<div style='margin-bottom:0.5rem;'></div>", unsafe_allow_html=True)

        # 🔴 AQUI estava o erro: faltava passar o hist_df e o nome do filtro estava confuso
        render_redacao_tab(
            redacao_stats_df,
            redacao_hist_df,
            filters_red,
        )


    with tab_ideb:
        render_ideb_tab(ideb_df)


if __name__ == "__main__":
    main()

