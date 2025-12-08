from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import pandas as pd
import streamlit as st

from .config import THEME, DISCIPLINE_OPTIONS, DEFAULT_METRIC_LABEL
from .data_loader import get_metric_column

# Cor de destaque vinda do tema (fallback para laranja)
try:
    ACCENT_COLOR = THEME.get("accent_color", "#f97316")
except Exception:
    ACCENT_COLOR = "#f97316"


# -------------------------------------------------------------------
# Estrutura dos filtros globais
# -------------------------------------------------------------------


@dataclass
class GlobalFilters:
    disciplina_label: str
    metric_column: str
    redes: Optional[List[str]]
    localizacoes: Optional[List[str]]
    ufs: Optional[List[str]]


# -------------------------------------------------------------------
# Renderização dos filtros (usado nas abas)
# -------------------------------------------------------------------


def render_global_filters(
    df: pd.DataFrame,
    key_prefix: str = "",
    show_metric: bool = True,
    default_metric_label: str = DEFAULT_METRIC_LABEL,
) -> GlobalFilters:

    """
    Renderiza filtros suspensos + seletor de métrica.

    `key_prefix` permite ter filtros independentes em cada aba
    (ex.: 'ov_' para Visão Geral, 'map_' para Mapa & Território).
    """
    # Opções disponíveis em cada coluna (se existirem)
    redes_opts: List[str] = []
    if "TIPO_ESCOLA" in df.columns:
        redes_opts = sorted(df["TIPO_ESCOLA"].dropna().unique().tolist())

    loc_opts: List[str] = []
    if "LOCALIZACAO" in df.columns:
        loc_opts = sorted(df["LOCALIZACAO"].dropna().unique().tolist())

    uf_opts: List[str] = []
    if "SG_UF_ESC" in df.columns:
        uf_opts = sorted(df["SG_UF_ESC"].dropna().unique().tolist())

    # Linha com 3 filtros suspensos
    col_rede, col_loc, col_uf = st.columns(3)

    with col_rede:
        rede_selected = _dropdown_multiselect(
            label="Rede de ensino",
            options=redes_opts,
            key=f"{key_prefix}f_rede_ensino",
            accent_color=ACCENT_COLOR,
        )

    with col_loc:
        loc_selected = _dropdown_multiselect(
            label="Localização da escola",
            options=loc_opts,
            key=f"{key_prefix}f_localizacao",
            accent_color=ACCENT_COLOR,
        )

    with col_uf:
        uf_selected = _dropdown_multiselect(
            label="UF da escola",
            options=uf_opts,
            key=f"{key_prefix}f_uf",
            accent_color=ACCENT_COLOR,
        )

        # Espaço entre filtros suspensos e (possível) seletor de métrica
    st.markdown(
        "<div style='height:0.75rem;'></div>",
        unsafe_allow_html=True,
    )

    if show_metric:
        # Título do seletor de métrica
        st.markdown(
            "<p style='text-align:center; font-size:0.85rem; "
            "color:var(--muted-text-color); margin-bottom:0.25rem;'>"
            "Disciplina / métrica"
            "</p>",
            unsafe_allow_html=True,
        )

        # Seletor de métrica com wrapper .metric-toggle (para o CSS)
        st.markdown("<div class='metric-toggle'>", unsafe_allow_html=True)
        metric_label = st.radio(
            "Selecione a disciplina / métrica",  # label acessível (escondido visualmente)
            options=[
                "Nota final",
                "Ciências da Natureza",
                "Ciências Humanas",
                "Linguagens e Códigos",
                "Matemática",
                "Redação",
            ],
            horizontal=True,
            key=f"{key_prefix}f_disciplina",
            label_visibility="collapsed",  # esconde o texto na UI
        )
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        # Não desenha nada na tela: métrica fica fixa
        metric_label = default_metric_label

    metric_col = get_metric_column(metric_label)

    redes = _normalize_selection(rede_selected, redes_opts)
    locs = _normalize_selection(loc_selected, loc_opts)
    ufs = _normalize_selection(uf_selected, uf_opts)

    return GlobalFilters(
        disciplina_label=metric_label,
        metric_column=metric_col,
        redes=redes,
        localizacoes=locs,
        ufs=ufs,
    )



# -------------------------------------------------------------------
# Recuperar filtros do session_state (se precisar em outra aba)
# -------------------------------------------------------------------


def get_filters_from_session(df: pd.DataFrame) -> GlobalFilters:
    """
    Reconstrói o objeto GlobalFilters a partir de st.session_state,
    sem desenhar widgets. Útil para outras abas reutilizarem os
    mesmos filtros.
    """
    redes_opts: List[str] = []
    if "TIPO_ESCOLA" in df.columns:
        redes_opts = sorted(df["TIPO_ESCOLA"].dropna().unique().tolist())

    loc_opts: List[str] = []
    if "LOCALIZACAO" in df.columns:
        loc_opts = sorted(df["LOCALIZACAO"].dropna().unique().tolist())

    uf_opts: List[str] = []
    if "SG_UF_ESC" in df.columns:
        uf_opts = sorted(df["SG_UF_ESC"].dropna().unique().tolist())

    redes_sel = st.session_state.get("f_rede_ensino", redes_opts)
    loc_sel = st.session_state.get("f_localizacao", loc_opts)
    uf_sel = st.session_state.get("f_uf", uf_opts)

    disciplina_label = st.session_state.get("f_disciplina", DEFAULT_METRIC_LABEL)
    metric_column = get_metric_column(disciplina_label)

    redes = _normalize_selection(redes_sel, redes_opts)
    locs = _normalize_selection(loc_sel, loc_opts)
    ufs = _normalize_selection(uf_sel, uf_opts)

    return GlobalFilters(
        disciplina_label=disciplina_label,
        metric_column=metric_column,
        redes=redes,
        localizacoes=locs,
        ufs=ufs,
    )


# -------------------------------------------------------------------
# Filtro suspenso (expander + multiselect)
# -------------------------------------------------------------------


def _dropdown_multiselect(
    label: str,
    options: List[str],
    key: str,
    accent_color: str,
) -> List[str]:
    """
    Multiselect dentro de um "filtro suspenso" (expander).

    Comportamento:
    - Quando todas as opções estão selecionadas -> expander fechado.
    - Quando há filtro ativo (seleção parcial ou vazia) -> expander aberto.
    """
    if not options:
        st.write(f"*Nenhuma opção disponível para {label}*")
        return []

    # Estado inicial: todas as opções selecionadas
    if key not in st.session_state:
        st.session_state[key] = list(options)

    # Seleção corrente (antes de desenhar o widget)
    current: List[str] = st.session_state[key]
    summary = _build_summary(label, current, options)

    # Filtro ativo? (seleção diferente de "todas")
    has_active_filter = 0 < len(current) < len(options) or len(current) == 0

    # Se filtro estiver ativo, mantemos o expander ABERTO
    with st.expander(summary, expanded=has_active_filter):
        st.multiselect(
            label,
            options=options,
            default=current,
            key=key,  # o próprio widget atualiza st.session_state[key]
        )

    # Após o widget, lemos o valor atualizado
    current = st.session_state.get(key, [])

    # Linha fina de realce quando o filtro está ativo
    active = 0 < len(current) < len(options)
    bar_color = accent_color if active else "transparent"
    st.markdown(
        f"<div style='height:3px; border-radius:999px; background-color:{bar_color}; "
        "margin-top:0.15rem;'></div>",
        unsafe_allow_html=True,
    )

    return current


def _build_summary(label: str, selected: List[str], options: List[str]) -> str:
    """Texto do cabeçalho do filtro suspenso."""
    if not options:
        return f"{label}: (sem dados)"
    if not selected or len(selected) == len(options):
        return f"{label}: Todos"
    if len(selected) == 1:
        return f"{label}: {selected[0]}"
    return f"{label}: Múltiplas seleções ({len(selected)})"


def _normalize_selection(selected: List[str], options: List[str]) -> Optional[List[str]]:
    """
    Converte a seleção em:
    - None  -> quando todas as opções estão selecionadas (sem filtro)
    - []    -> quando nada está selecionado (filtro que zera)
    - lista -> seleção parcial (filtro aplicado)
    """
    if not options:
        return None
    if not selected:
        return []
    if len(selected) == len(options):
        return None
    return selected


# -------------------------------------------------------------------
# Aplicação dos filtros em um dataframe linha a linha
# -------------------------------------------------------------------


def apply_filters(df: pd.DataFrame, filters: GlobalFilters) -> pd.DataFrame:
    """
    Função utilitária para aplicar os filtros globais
    em um dataframe em nível de linha (se for necessário em outras abas).
    """
    filtered = df.copy()

    if filters.redes and "TIPO_ESCOLA" in filtered.columns:
        filtered = filtered[filtered["TIPO_ESCOLA"].isin(filters.redes)]

    if filters.localizacoes and "LOCALIZACAO" in filtered.columns:
        filtered = filtered[filtered["LOCALIZACAO"].isin(filters.localizacoes)]

    if filters.ufs and "SG_UF_ESC" in filtered.columns:
        filtered = filtered[filtered["SG_UF_ESC"].isin(filters.ufs)]

    if filters.metric_column in filtered.columns:
        filtered = filtered.dropna(subset=[filters.metric_column])

    return filtered
