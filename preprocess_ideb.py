from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data_loader import DATA_DIR, PROCESSED_DIR


EXCEL_NAME = "divulgacao_brasil_ideb_2023.xlsx"
SHEET_NAME = "Brasil (EM) ajustado"


def main() -> None:
    excel_path = DATA_DIR / EXCEL_NAME
    if not excel_path.exists():
        raise FileNotFoundError(
            f"Arquivo {excel_path} não encontrado.\n"
            f"Coloque '{EXCEL_NAME}' dentro da pasta 'data/'."
        )

    print(f"Lendo Excel: {excel_path}")
    # header=4 como no notebook (linha que contém 'Rede', '2005', '2007', ...)
    df = pd.read_excel(excel_path, sheet_name=SHEET_NAME, header=4)

    # Mantém apenas as redes de interesse
    df = df[df["Rede"].isin(["Pública", "Privada"])].copy()

    # Colunas que representam anos (ex.: 2005, 2007, ..., 2023)
    year_cols = [c for c in df.columns if str(c).isdigit()]
    if not year_cols:
        raise ValueError("Não encontrei colunas de anos (2005, 2007, etc.) no Excel.")

    # Deixa só Rede + anos
    df_years = df[["Rede"] + year_cols].copy()

    # Converte para formato longo: uma linha por (Rede, Ano)
    df_long = df_years.melt(
        id_vars="Rede",
        value_vars=year_cols,
        var_name="Ano",
        value_name="IDEB_Score",
    )

    df_long["Ano"] = df_long["Ano"].astype(str)
    df_long["IDEB_Score"] = pd.to_numeric(df_long["IDEB_Score"], errors="coerce")
    df_long = df_long.dropna(subset=["IDEB_Score"])

    out_path = PROCESSED_DIR / "ideb_brasil_em.parquet"
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df_long.to_parquet(out_path, index=False)
    print("Arquivo salvo em:", out_path)


if __name__ == "__main__":
    main()
