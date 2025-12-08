from __future__ import annotations

# Paleta base do painel (tema escuro suave)
THEME = {
    # Cores principais
    "primary_color": "#38bdf8",          # azul ciano (links, detalhes)
    "accent_color": "#f97316",           # laranja (botão de métrica, destaques)
    "background_color": "#020617",       # fundo geral (quase preto azulado)
    "card_background": "#0b1120",        # fundo dos cards / caixas
    "secondary_background": "#020617",   # pode usar para outros blocos

    # Texto
    "text_color": "#e5e7eb",             # texto principal (cinza bem claro)
    "muted_text_color": "#9ca3af",       # texto secundário
    "muted_border_color": "#1f2937",     # bordas discretas

    # Outros
    "danger_color": "#f97373",
    "border_radius": "0.75rem",
}

# Caminho da logo (ajuste o nome se quiser outro arquivo)
LOGO_PATH = "assets/marca ceub versao negativa lilas.png"

# Mapeamento das métricas/disciplinas
DISCIPLINE_OPTIONS = {
    "Nota final": "nota_final",
    "Ciências da Natureza": "NU_NOTA_CN",
    "Ciências Humanas": "NU_NOTA_CH",
    "Linguagens e Códigos": "NU_NOTA_LC",
    "Matemática": "NU_NOTA_MT",
    "Redação": "NU_NOTA_REDACAO",
}

DEFAULT_METRIC_LABEL = "Nota final"
