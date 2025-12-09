
# Painel ENEM 2024 – Streamlit

Painel interativo para exploração dos resultados do ENEM 2024, com foco em
desigualdades entre **redes de ensino**, **territórios** e **resultados de redação**.

---

## 🔗 Acesse o painel online

O painel está disponível publicamente em:

👉 **https://hermesjasper-painel-streamlit-enem-2024--app-mkvies.streamlit.app/**

---

## 🎯 Objetivos do projeto

- Oferecer uma **visão geral clara e visual** do desempenho no ENEM 2024.  
- Comparar **redes de ensino** (pública x privada x federal x municipal).  
- Explorar desigualdades **entre estados (UF) e localização das escolas**.  
- Destacar indicadores críticos de **Redação** (provas zeradas, notas muito altas).  
- Conectar os resultados do ENEM com a **evolução do IDEB no Ensino Médio**.

---

## 🧭 Abas do painel

### 1. Visão Geral
- Indicadores principais:
  - Nota média (nota final).
  - Número de participantes.
  - Diferença de nota entre rede pública e rede privada.
  - % de participantes da rede privada.
- Filtros combináveis:
  - **Rede de ensino**, **localização da escola** e **UF**.
  - Seleção da **disciplina/métrica** (nota final e áreas específicas).
- Distribuição das notas por faixas (histograma).
- Participação por tipo de escola.

### 2. Mapa & Território
- Mapa do Brasil com **nota média por UF**.
- Ranking dos estados (UF) segundo a métrica selecionada.
- Destaque para:
  - Maior e menor nota média entre estados.
  - Nota média nacional.

### 3. Escolas & Desigualdades
- Distribuição das **notas médias das escolas** por rede de ensino.
- Histogramas empilhados por tipo de rede, para comparar perfis de desempenho.
- Indicadores agregados por escola:
  - Média da nota final.
  - Nº de participantes por escola.
  - Diferença de desempenho entre redes.

### 4. Redação
- Indicadores específicos:
  - **% de provas de redação zeradas**.
  - **% de provas com nota ≥ 900**.
- Comparações por rede de ensino, localização e UF.
- Gráficos que ajudam a visualizar extremos de desempenho em redação.

### 5. Linha do Tempo IDEB
- Série histórica do **IDEB do Ensino Médio – Brasil**:
  - Rede pública.
  - Rede privada.
- Destaque para:
  - Nota IDEB da rede pública no último ano disponível.
  - Nota IDEB da rede privada no último ano.
  - Diferença entre redes.
- Gráfico de linhas com:
  - Linhas mais grossas e pontos destacados.
  - Fundo adaptado ao tema escuro para facilitar o contraste das séries.

---

## 📊 Fonte de dados

- **Resultado do ENEM 2024** – arquivos oficiais com microdados consolidados
  (tratados e convertidos para `.parquet` para melhor desempenho).
- **Base de participantes/escolas** – utilizada para agregar notas por escola,
  rede de ensino, localização e UF.
- **IDEB** – série histórica do IDEB para o Ensino Médio (Brasil) por rede de
  ensino.

Os arquivos tratados são armazenados na pasta `data/` e, após o pré-processamento,
os resultados agregados vão para `data/processed/`.

---

## 🛠️ Tecnologias

- Python 3.11+
- Streamlit
- Pandas
- NumPy
- Plotly
- Formato de dados: **CSV** e **Parquet**

---

## 🧱 Estrutura simplificada do projeto

```text
Painel-Streamlit-ENEM-2024-/
├─ app.py                    # Arquivo principal do Streamlit
├─ requirements.txt          # Dependências do projeto
├─ data/
│  ├─ RESULTADOS_2024.csv / .parquet
│  ├─ enem_map_uf.parquet
│  ├─ participantes.csv
│  └─ processed/
│     ├─ overview_stats.parquet
│     ├─ overview_hist.parquet
│     ├─ enem_map_uf.parquet
│     ├─ schools_stats.parquet
│     └─ redacao_stats.parquet
└─ src/
   ├─ config.py              # Tema, cores e mapeamentos
   ├─ data_loader.py         # Funções de leitura das bases processadas
   ├─ filters.py             # Filtros globais reutilizáveis
   ├─ overview_tab.py        # Lógica/visual da aba Visão Geral
   ├─ map_tab.py             # Lógica/visual da aba Mapa & Território
   ├─ schools_tab.py         # Lógica/visual da aba Escolas & Desigualdades
   ├─ redacao_tab.py         # Lógica/visual da aba Redação
   └─ utils.py               # Funções auxiliares (tema, CSS etc.)
```

Scripts de pré-processamento (na raiz do projeto):

- `preprocess_overview.py`
- `preprocess_map.py` (ou `preprocess_map_uf.py`, conforme o nome final)
- `preprocess_schools.py`
- `preprocess_redacao.py`

---

## ▶️ Como rodar o projeto localmente

### 1. Clonar o repositório

```bash
git clone https://github.com/hermesjasper/Painel-Streamlit-ENEM-2024-.git
cd Painel-Streamlit-ENEM-2024-
```

### 2. Criar e ativar o ambiente virtual (opcional, mas recomendado)

```bash
python -m venv .venv
.\.venv\Scriptsctivate      # Windows
# source .venv/bin/activate  # Linux/Mac
```

### 3. Instalar as dependências

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Rodar os scripts de pré-processamento

```bash
python preprocess_overview.py
python preprocess_map.py
python preprocess_schools.py
python preprocess_redacao.py
```

### 5. Subir o app Streamlit

```bash
streamlit run app.py
```

O painel ficará disponível em: `http://localhost:8501`.

---

## 🚀 Deploy

O deploy deste painel foi feito no **Streamlit Community Cloud**, conectado a
este repositório GitHub.

A cada novo **push** na branch principal, o Streamlit:

- atualiza o código do repositório,
- reinstala as dependências,
- e executa o `app.py`.

O link público é:

👉 **https://hermesjasper-painel-streamlit-enem-2024--app-mkvies.streamlit.app/**

---

## 👥 Autores

Projeto desenvolvido como trabalho de Visualização de Dados – CEUB.

- **Hermes Winarski**
- **Leonardo Amaral**
- **Marcelo**
- **Matheus Lira**
