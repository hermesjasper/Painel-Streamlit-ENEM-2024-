from __future__ import annotations

from typing import List

import pandas as pd

from src.data_loader import preprocess_enem_df, DATA_DIR, PROCESSED_DIR
from src.config import DISCIPLINE_OPTIONS


INPUT_PARQUET = DATA_DIR / "RESULTADOS_2024.parquet"
OUTPUT_PARQUET = PROCESSED_DIR / "enem_map_uf.parquet"


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # 1) Lê a mesma base bruta da Aba 1
    if not INPUT_PARQUET.exists():
        raise FileNotFoundError(f"Parquet base não encontrado em: {INPUT_PARQUET}")
    print(f"Lendo base: {INPUT_PARQUET}")
    df = pd.read_parquet(INPUT_PARQUET)

    # 2) Aplica o MESMO pré-processamento da Aba 1
    df = preprocess_enem_df(df)

    # 3) Seleciona as colunas usadas nas abas
    cols_base = ["TIPO_ESCOLA", "LOCALIZACAO", "SG_UF_ESC"]
    metric_cols: List[str] = [
        c for c in DISCIPLINE_OPTIONS.values() if c in df.columns
    ]
    needed_cols = cols_base + metric_cols
    df = df[needed_cols]

    # 4) Usa apenas linhas com nota_final válida – igual à Aba 1
    df = df.dropna(subset=["nota_final"]).copy()

    # 5) Remove UFs nulas (não fazem sentido no mapa)
    df = df.dropna(subset=["SG_UF_ESC"])

    group_cols = ["SG_UF_ESC", "TIPO_ESCOLA", "LOCALIZACAO"]

    # 6) Agrega de forma consistente com overview_stats
    agg_dict = {
        "n_participantes": ("nota_final", "size"),
    }
    for col in metric_cols:
        agg_dict[f"sum_{col}"] = (col, "sum")

    print("Agregando por UF, rede de ensino e localização...")
    agg = (
        df.groupby(group_cols, dropna=False)
        .agg(**agg_dict)
        .reset_index()
        .astype({"n_participantes": "int64"})
    )

    print(f"Salvando tabela resumida em: {OUTPUT_PARQUET}")
    agg.to_parquet(OUTPUT_PARQUET, index=False)

    print("Pré-processamento da Aba 2 concluído!")


if __name__ == "__main__":
    main()
