from __future__ import annotations

from typing import List

import numpy as np
import pandas as pd

from src.data_loader import preprocess_enem_df, DATA_DIR, PROCESSED_DIR


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    df = load_raw_enem()
    df = preprocess_enem_df(df)

    # Só seguimos se existir coluna de redação
    if "NU_NOTA_REDACAO" not in df.columns:
        raise ValueError("Coluna NU_NOTA_REDACAO não encontrada na base.")

    # Dimensões usadas nos filtros globais
    group_cols = ["TIPO_ESCOLA", "LOCALIZACAO", "SG_UF_ESC"]

    # Mantém apenas colunas necessárias
    needed_cols: List[str] = group_cols + ["NU_NOTA_REDACAO"]
    df = df[needed_cols].copy()

    # Remove linhas sem nota de redação
    df = df.dropna(subset=["NU_NOTA_REDACAO"])

    # -----------------------------
    # Tabela de estatísticas
    # -----------------------------
    agg_dict = {
        "n": ("NU_NOTA_REDACAO", "size"),
        "sum_redacao": ("NU_NOTA_REDACAO", "sum"),
        "n_zero": ("NU_NOTA_REDACAO", lambda s: (s == 0).sum()),
        "n_900mais": ("NU_NOTA_REDACAO", lambda s: (s >= 900).sum()),
    }

    stats = df.groupby(group_cols, dropna=False).agg(**agg_dict).reset_index()
    stats["media_redacao"] = stats["sum_redacao"] / stats["n"]

    stats_path = PROCESSED_DIR / "redacao_stats.parquet"
    stats.to_parquet(stats_path, index=False)
    print("Arquivo salvo:", stats_path)

    # -----------------------------
    # Tabela de histograma
    # -----------------------------
    bin_edges = np.linspace(0, 1000, num=41)  # 25 pontos em 0–1000
    bin_left = bin_edges[:-1]
    bin_right = bin_edges[1:]

    records = []

    for _, sub in df.groupby(group_cols):
        dims = {
            "TIPO_ESCOLA": sub["TIPO_ESCOLA"].iloc[0],
            "LOCALIZACAO": sub["LOCALIZACAO"].iloc[0],
            "SG_UF_ESC": sub["SG_UF_ESC"].iloc[0],
        }

        vals = sub["NU_NOTA_REDACAO"].dropna().values
        if len(vals) == 0:
            continue

        counts, _ = np.histogram(vals, bins=bin_edges)

        for i, count in enumerate(counts):
            if count == 0:
                continue
            records.append(
                {
                    **dims,
                    "bin_idx": i,
                    "bin_left": float(bin_left[i]),
                    "bin_right": float(bin_right[i]),
                    "count": int(count),
                }
            )

    hist = pd.DataFrame.from_records(records)
    hist_path = PROCESSED_DIR / "redacao_hist.parquet"
    hist.to_parquet(hist_path, index=False)
    print("Arquivo salvo:", hist_path)

    print("Pré-processamento da Aba Redação concluído.")


def load_raw_enem() -> pd.DataFrame:
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


if __name__ == "__main__":
    main()
