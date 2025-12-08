
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional

import pandas as pd
import streamlit as st

from .config import DISCIPLINE_OPTIONS


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PROCESSED_DIR = DATA_DIR / "processed"


def _ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


@st.cache_data(show_spinner="Carregando dados brutos do ENEM 2024...")
def load_enem_data(columns: Optional[Iterable[str]] = None) -> pd.DataFrame:
    _ensure_dirs()
    parquet_path = DATA_DIR / "RESULTADOS_2024.parquet"
    csv_path = DATA_DIR / "RESULTADOS_2024.csv"

    if parquet_path.exists():
        df = pd.read_parquet(parquet_path, columns=columns)
    elif csv_path.exists():
        read_kwargs = {"sep": ";", "encoding": "iso-8859-1"}
        if columns is not None:
            read_kwargs["usecols"] = list(columns)
        df = pd.read_csv(csv_path, **read_kwargs)
        try:
            df.to_parquet(parquet_path, index=False)
        except Exception:
            pass
    else:
        st.error(
            "Nenhum arquivo de dados encontrado em 'data/'. "
            "Adicione 'RESULTADOS_2024.csv' ou 'RESULTADOS_2024.parquet'."
        )
        st.stop()

    df = preprocess_enem_df(df)
    return df


@st.cache_data(show_spinner="Carregando resumos da Aba 1...")
def load_overview_stats() -> pd.DataFrame:
    _ensure_dirs()
    path = PROCESSED_DIR / "overview_stats.parquet"
    if not path.exists():
        st.error(
            "Arquivo 'overview_stats.parquet' não encontrado em 'data/processed/'. "
            "Rode o script 'preprocess_enem.py' antes de abrir o painel."
        )
        st.stop()
    return pd.read_parquet(path)


@st.cache_data(show_spinner="Carregando histogramas da Aba 1...")
def load_overview_hist() -> pd.DataFrame:
    _ensure_dirs()
    path = PROCESSED_DIR / "overview_hist.parquet"
    if not path.exists():
        st.error(
            "Arquivo 'overview_hist.parquet' não encontrado em 'data/processed/'. "
            "Rode o script 'preprocess_enem.py' antes de abrir o painel."
        )
        st.stop()
    return pd.read_parquet(path)


def preprocess_enem_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "nota_final" not in df.columns:
        colunas_notas = [
            "NU_NOTA_CN",
            "NU_NOTA_CH",
            "NU_NOTA_LC",
            "NU_NOTA_MT",
            "NU_NOTA_REDACAO",
        ]
        available_cols = [c for c in colunas_notas if c in df.columns]
        if available_cols:
            df["nota_final"] = df[available_cols].mean(axis=1)

    if "nota_final" in df.columns:
        df = df.dropna(subset=["nota_final"]).copy()

    if "TP_DEPENDENCIA_ADM_ESC" in df.columns:
        mapa_dependencia = {1: "Federal", 2: "Estadual", 3: "Municipal", 4: "Privada"}
        df["TIPO_ESCOLA"] = df["TP_DEPENDENCIA_ADM_ESC"].map(mapa_dependencia)

    if "TP_STATUS_REDACAO" in df.columns:
        mapa_status = {
            1: "1. Sem Problemas (Válida)",
            2: "2. Anulada",
            3: "3. Cópia T. Motivador",
            4: "4. Não Atribuída/Em Branco",
            5: "5. Zero por Critério (Grave)",
            6: "6. Cancelada",
            9: "7. Outras Causas/Fuga",
        }
        df["STATUS_REDACAO"] = df["TP_STATUS_REDACAO"].map(mapa_status)

    if "TP_LOCALIZACAO_ESC" in df.columns:
        mapa_localizacao = {1: "Urbana", 2: "Rural"}
        df["LOCALIZACAO"] = df["TP_LOCALIZACAO_ESC"].map(mapa_localizacao)

    if {"NO_MUNICIPIO_ESC", "SG_UF_ESC"} <= set(df.columns):
        df["MUNICIPIO_UF"] = (
            df["NO_MUNICIPIO_ESC"].astype(str)
            + " - "
            + df["SG_UF_ESC"].astype(str)
        )

    if "CO_UF_ESC" in df.columns:
        df["CO_UF_ESC"] = df["CO_UF_ESC"].astype("Int64")

    for col in df.select_dtypes(include=["float64"]).columns:
        df[col] = pd.to_numeric(df[col], downcast="float")
    for col in df.select_dtypes(include=["int64"]).columns:
        df[col] = pd.to_numeric(df[col], downcast="integer")

    return df


def get_metric_column(metric_label: str) -> str:
    return DISCIPLINE_OPTIONS.get(metric_label, "nota_final")

@st.cache_data
def load_map_uf_data() -> pd.DataFrame:
    """
    Carrega a tabela resumida para a aba Mapa & Território.

    Arquivo gerado por scripts/preprocess_map_uf.py
    """
    path = Path("data/enem_map_uf.parquet")
    if not path.exists():
        raise FileNotFoundError(
            "Arquivo data/enem_map_uf.parquet não encontrado. "
            "Execute scripts/preprocess_map_uf.py antes de abrir o painel."
        )
    return pd.read_parquet(path)

@st.cache_data
def load_schools_stats() -> pd.DataFrame:
    """
    Carrega a tabela agregada por escola gerada pelo preprocess_schools.py.
    """
    path = PROCESSED_DIR / "schools_stats.parquet"
    if not path.exists():
        raise FileNotFoundError(
            f"Arquivo 'schools_stats.parquet' não encontrado em {path}.\n"
            "Rode antes: python preprocess_schools.py"
        )
    return pd.read_parquet(path)

def load_redacao_stats() -> pd.DataFrame:
    path = PROCESSED_DIR / "redacao_stats.parquet"
    if not path.exists():
        raise FileNotFoundError(
            f"Arquivo {path} não encontrado. Rode 'python preprocess_redacao.py' primeiro."
        )
    return pd.read_parquet(path)


def load_redacao_hist() -> pd.DataFrame:
    path = PROCESSED_DIR / "redacao_hist.parquet"
    if not path.exists():
        raise FileNotFoundError(
            f"Arquivo {path} não encontrado. Rode 'python preprocess_redacao.py' primeiro."
        )
    return pd.read_parquet(path)

def load_schools_data() -> pd.DataFrame:
    """
    Carrega a tabela resumida usada na aba 'Escolas & Desigualdades'.

    O arquivo é gerado pelo script preprocess_schools.py:
        python preprocess_schools.py
    """
    path = PROCESSED_DIR / "schools_stats.parquet"
    if not path.exists():
        raise FileNotFoundError(
            f"Arquivo {path} não encontrado. Rode 'python preprocess_schools.py' primeiro."
        )
    return pd.read_parquet(path)

def load_ideb_brasil_em() -> pd.DataFrame:
    """
    Carrega a série histórica do IDEB (Ensino Médio - Brasil),
    agregada por Rede de ensino (Pública / Privada).

    Arquivo gerado por preprocess_ideb.py.
    """
    path = PROCESSED_DIR / "ideb_brasil_em.parquet"
    if not path.exists():
        raise FileNotFoundError(
            f"Arquivo {path} não encontrado. Rode 'python preprocess_ideb.py' primeiro."
        )
    return pd.read_parquet(path)
