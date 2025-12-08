from __future__ import annotations

from pathlib import Path
from typing import List, Tuple, Optional

import pandas as pd

from src.data_loader import (
    DATA_DIR,
    PROCESSED_DIR,
    preprocess_enem_df,  # mesmo pipeline da Aba 1
)
from src.config import DISCIPLINE_OPTIONS


# Métricas usadas (mesmas da config)
METRIC_COLUMNS: List[str] = sorted(set(DISCIPLINE_OPTIONS.values()))


def main() -> None:
    """
    Gera uma tabela agregada por escola para a Aba 3 (Escolas & Desigualdades).

    Saída: PROCESSED_DIR / "schools_stats.parquet"

    Cada linha representa uma escola e traz:
      - school_id, school_name (se existir),
      - TIPO_ESCOLA, LOCALIZACAO, SG_UF_ESC,
      - n_participantes,
      - média de cada métrica (media_nota_final, media_NU_NOTA_CN, etc.).
    """

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    df_raw = load_raw_enem()
    # 🔹 Aqui aplicamos o MESMO pré-processamento da Aba 1
    df = preprocess_enem_df(df_raw)

    # Agora sim essas colunas devem existir
    required_base = {"TIPO_ESCOLA", "LOCALIZACAO", "SG_UF_ESC", "nota_final"}
    required_metrics = set(METRIC_COLUMNS)
    required_all = required_base | required_metrics

    missing = required_all.difference(df.columns)
    if missing:
        raise ValueError(
            "Colunas faltando na base para o pré-processamento da Aba 3 "
            "(já após preprocess_enem_df):\n"
            f"{missing}"
        )

    # Detecta automaticamente colunas de ID e nome da escola
    school_id_col, school_name_col = _detect_school_cols(df)

    print(f"Usando coluna de ID de escola: {school_id_col}")
    if school_name_col:
        print(f"Usando coluna de NOME de escola: {school_name_col}")
    else:
        print("Nenhuma coluna de nome de escola encontrada; seguiremos só com o ID.")

    # Remove linhas sem ID de escola
    df = df.dropna(subset=[school_id_col])

    # Colunas de agrupamento
    group_cols = [school_id_col]
    if school_name_col:
        group_cols.append(school_name_col)
    group_cols.extend(["TIPO_ESCOLA", "LOCALIZACAO", "SG_UF_ESC"])

    # Agregações:
    # - n_participantes: número de estudantes na escola
    # - média de cada métrica de nota
    agg_dict = {
        "n_participantes": ("nota_final", "size"),
    }
    for col in METRIC_COLUMNS:
        if col in df.columns:
            agg_dict[f"media_{col}"] = (col, "mean")

    print("Agregando por escola...")
    agg = (
        df.groupby(group_cols, dropna=False)
        .agg(**agg_dict)
        .reset_index()
        .astype({"n_participantes": "int64"})
    )

    # Padroniza nomes para facilitar na aba
    rename_map = {school_id_col: "school_id"}
    if school_name_col:
        rename_map[school_name_col] = "school_name"
    agg = agg.rename(columns=rename_map)

    output_path = PROCESSED_DIR / "schools_stats.parquet"
    print(f"Salvando tabela agregada por escola em: {output_path}")
    agg.to_parquet(output_path, index=False)

    print("Pré-processamento da Aba 3 concluído!")


def load_raw_enem() -> pd.DataFrame:
    """
    Lê o arquivo bruto do ENEM (parquet ou csv) da pasta data/.
    """
    parquet_path = DATA_DIR / "RESULTADOS_2024.parquet"
    csv_path = DATA_DIR / "RESULTADOS_2024.csv"

    if parquet_path.exists():
        df = pd.read_parquet(parquet_path)
    elif csv_path.exists():
        df = pd.read_csv(csv_path, sep=";", encoding="iso-8859-1")
    else:
        raise FileNotFoundError(
            "Coloque RESULTADOS_2024.csv ou RESULTADOS_2024.parquet na pasta 'data/'."
        )
    return df


def _detect_school_cols(df: pd.DataFrame) -> Tuple[str, Optional[str]]:
    """
    Tenta identificar automaticamente ID e nome da escola.

    Se não encontrar nenhuma coluna de ID plausível, lança um erro com mensagem clara.
    """
    id_candidates = [
        "CO_ESCOLA",
        "ID_ESCOLA",
        "COD_ESCOLA",
        "ESCOLA_ID",
        "CO_ENTIDADE",
    ]
    name_candidates = [
        "NO_ESCOLA",
        "NOME_ESCOLA",
        "NM_ESCOLA",
    ]

    school_id_col = next((c for c in id_candidates if c in df.columns), None)
    if school_id_col is None:
        raise ValueError(
            "Não consegui identificar a coluna de ID da escola.\n"
            "Verifique na sua base o nome real (ex.: CO_ESCOLA, CO_ENTIDADE) "
            "e adicione em _detect_school_cols()."
        )

    school_name_col = next((c for c in name_candidates if c in df.columns), None)
    return school_id_col, school_name_col


if __name__ == "__main__":
    main()
