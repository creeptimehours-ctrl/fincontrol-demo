---
title: FinControl - Sistema Financeiro (Demo)
emoji: 💳
colorFrom: blue
colorTo: indigo
sdk: streamlit
app_file: app.py
pinned: false
---

# FinControl — Sistema Financeiro (Python + Streamlit + SQLite)

Sistema de controle de finanças pessoais com cadastro de usuários, receitas,
despesas, metas financeiras e dashboard.

## Status

- [x] **Fase 1 — Demonstração** (atual): interface completa com dados fictícios,
      independente do banco de dados real. Layout alinhado à referência do
      cliente: tema escuro, transações com edição/exclusão por ID e metas com
      expander "Criar nova meta".
- [ ] **Fase 2 — Versão contratada**: autenticação real (senha com hash),
      persistência em SQLite, suíte de testes Pytest.
- [ ] **Fase 3 — Publicação**: deploy (Streamlit Cloud) + README final do cliente.

## Como rodar

```bash
# 1. instalar dependências (uma única vez)
pip install -r requirements.txt

# 2. iniciar a aplicação
streamlit run app.py
```

O navegador abre em `http://localhost:8501`.
Na tela de login, clique em **Entrar** (usuário/senha já preenchidos — modo
demonstração aceita qualquer valor).

## Estrutura

| Arquivo | Responsabilidade |
|---|---|
| `app.py` | Interface Streamlit (login, dashboard, transações, metas) |
| `core.py` | Regras de negócio puras — validação, cálculos, formatação pt-BR |
| `demo_data.py` | Dados fictícios determinísticos da demonstração |
| `.streamlit/config.toml` | Tema visual (escuro, conforme referência do cliente) |
| `requirements.txt` | Dependências |
| `verify_demo.py` | Teste automatizado da demo (9 verificações, roda com `python verify_demo.py`) |

## Telas

- **Dashboard** — saldo, receitas/despesas do mês (com comparação ao mês
  anterior), taxa de economia, evolução do saldo e despesas por categoria.
- **Transações** — tabela com filtro por tipo, cadastro, edição completa
  (descrição, categoria, tipo, valor, data) e exclusão com confirmação.
- **Metas** — cards com barra de progresso, aporte, criação via expander
  "Criar nova meta" e mensagem de estado vazio.

## Tecnologias

Python 3.11 · Streamlit · SQLite (fase 2) · Pandas · Plotly · Pytest (fase 2)

## Gravar a demo (para proposta)

1. `streamlit run app.py`
2. Grave em tela cheia (OBS ou o gravador nativo do Windows — `Win + G`):
   login → dashboard → criar receita → criar despesa → aportar em meta.
3. ~60 segundos bastam.
