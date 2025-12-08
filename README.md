
# Painel ENEM 2024 – v4

- Aba 1 usa tabelas resumidas (`overview_stats.parquet` e `overview_hist.parquet`).
- Filtros de Rede, Localização e UF em estilo "suspenso" (expander):
  - "<label>: Todos" quando tudo está selecionado;
  - "<label>: <nome>" quando há apenas uma seleção;
  - "<label>: Múltiplas seleções (N)" quando há seleção parcial.
- Linha fina colorida sob o filtro quando ativo.
- Seleção de disciplina/métrica em botões tipo pílula.
- Gráficos de distribuição e participação lado a lado.

## Uso

1. Coloque `RESULTADOS_2024.csv` ou `RESULTADOS_2024.parquet` em `data/`.
2. Gere os parquets resumidos:

   ```bash
   python preprocess_enem.py
   ```

3. Instale dependências e rode o app:

   ```bash
   pip install -r requirements.txt
   streamlit run app.py
   ```
