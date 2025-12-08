
from __future__ import annotations

from typing import List

import numpy as np
import pandas as pd

from src.data_loader import preprocess_enem_df, DATA_DIR, PROCESSED_DIR
from src.config import DISCIPLINE_OPTIONS


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    df = load_raw_enem()
    df = preprocess_enem_df(df)

    cols_base = ["TIPO_ESCOLA", "LOCALIZACAO", "SG_UF_ESC"]
    metric_cols = [c for c in DISCIPLINE_OPTIONS.values() if c in df.columns]

    needed_cols = cols_base + metric_cols
    df = df[needed_cols].dropna(subset=["nota_final"]).copy()

    build_overview_stats(df, metric_cols)
    build_overview_hist(df, metric_cols)

    print("Pré-processamento da Aba 1 concluído.")


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


def build_overview_stats(df: pd.DataFrame, metric_cols: List[str]) -> None:
    group_cols = ["TIPO_ESCOLA", "LOCALIZACAO", "SG_UF_ESC"]

    agg_dict = {"n": ("nota_final", "size")}
    for col in metric_cols:
        agg_dict[f"sum_{col}"] = (col, "sum")

    stats = df.groupby(group_cols).agg(**agg_dict).reset_index()
    out_path = PROCESSED_DIR / "overview_stats.parquet"
    stats.to_parquet(out_path, index=False)
    print("Arquivo salvo:", out_path)


def build_overview_hist(df: pd.DataFrame, metric_cols: List[str]) -> None:
    group_cols = ["TIPO_ESCOLA", "LOCALIZACAO", "SG_UF_ESC"]

    bin_edges = np.linspace(0, 1000, num=41)
    bin_left = bin_edges[:-1]
    bin_right = bin_edges[1:]

    records = []

    for _, sub in df.groupby(group_cols):
        dims = {
            "TIPO_ESCOLA": sub["TIPO_ESCOLA"].iloc[0],
            "LOCALIZACAO": sub["LOCALIZACAO"].iloc[0],
            "SG_UF_ESC": sub["SG_UF_ESC"].iloc[0],
        }

        for metric in metric_cols:
            vals = sub[metric].dropna().values
            if len(vals) == 0:
                continue

            counts, _ = np.histogram(vals, bins=bin_edges)

            for i, count in enumerate(counts):
                if count == 0:
                    continue
                records.append(
                    {
                        **dims,
                        "metric": metric,
                        "bin_idx": i,
                        "bin_left": float(bin_left[i]),
                        "bin_right": float(bin_right[i]),
                        "count": int(count),
                    }
                )

    hist = pd.DataFrame.from_records(records)
    out_path = PROCESSED_DIR / "overview_hist.parquet"
    hist.to_parquet(out_path, index=False)
    print("Arquivo salvo:", out_path)


if __name__ == "__main__":
    main()
