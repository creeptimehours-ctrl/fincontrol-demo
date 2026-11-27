# app.py | Interface do Sistema Financeiro - Streamlit (modo demonstracao) | Python 3.11
# Executar com: streamlit run app.py
# A demo usa apenas dados ficticios (demo_data.py) - nenhuma escrita em banco real.
# Layout alinhado a referencia do cliente: tema escuro, transacoes com
# edicao/exclusao por ID e metas com expander de criacao.

from __future__ import annotations

from dataclasses import replace as substituir
from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from core import (
    CATEGORIAS_DESPESA,
    CATEGORIAS_RECEITA,
    TIPO_DESPESA,
    TIPO_RECEITA,
    Lancamento,
    Meta,
    despesas_por_categoria,
    evolucao_saldo,
    formatar_data,
    formatar_moeda,
    progresso_meta,
    totais,
    totais_do_mes,
    validar_lancamento,
)
from demo_data import USUARIO_DEMO, gerar_lancamentos, gerar_metas

st.set_page_config(
    page_title="FinControl - Sistema Financeiro",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        h1 {font-weight: 700; letter-spacing: -0.4px;}
        div[data-testid="stMetric"] {
            background: #161b24;
            border: 1px solid #262d3a;
            border-radius: 14px;
            padding: 14px 18px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.35);
        }
        div[data-testid="stMetricLabel"] {color: #8a94a8;}
        div[data-testid="stMetricValue"] {font-weight: 700;}
        section[data-testid="stSidebar"] {border-right: 1px solid #232936;}
        .demo-badge {
            display: inline-block;
            background: #2b2110;
            color: #ffb35e;
            border: 1px solid #7a4a12;
            border-radius: 999px;
            padding: 3px 12px;
            font-size: 0.82rem;
            font-weight: 600;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

PAGINAS = ["Dashboard", "Transações", "Metas"]


# --------------------------------------------------------------------------
# Estado da sessao
# --------------------------------------------------------------------------
def _iniciar_estado() -> None:
    """Popula a session_state com a demo na primeira execucao."""
    if "logado" not in st.session_state:
        st.session_state.logado = False
    if "usuario" not in st.session_state:
        st.session_state.usuario = USUARIO_DEMO
    if "lancamentos" not in st.session_state:
        st.session_state.lancamentos = gerar_lancamentos()
    if "metas" not in st.session_state:
        st.session_state.metas = gerar_metas()


def _novo_id() -> int:
    ids = [l.id for l in st.session_state.lancamentos]
    return max(ids) + 1 if ids else 1


def _nova_id_meta() -> int:
    ids = [m.id for m in st.session_state.metas]
    return max(ids) + 1 if ids else 1


def _sair() -> None:
    st.session_state.logado = False


def _mes_anterior(ref: date) -> date:
    if ref.month == 1:
        return date(ref.year - 1, 12, 1)
    return date(ref.year, ref.month - 1, 1)


def _opcao_de_transacao(tx: Lancamento) -> str:
    """Rotulo no estilo da referencia: '#1 - investimento (2026-11-25)'."""
    return f"#{tx.id} — {tx.descricao} ({tx.data.isoformat()})"


def _id_da_opcao(opcao: str) -> int:
    return int(opcao.split("—")[0].strip().lstrip("#"))


def _por_id(lista: list[Lancamento], tid: int) -> Lancamento | None:
    return next((l for l in lista if l.id == tid), None)


def _carregar_edicao(tx: Lancamento) -> None:
    """Carrega a transacao selecionada nos campos de edicao."""
    st.session_state["ed_id"] = tx.id
    st.session_state["ed_descricao"] = tx.descricao
    st.session_state["ed_categoria"] = tx.categoria
    st.session_state["ed_tipo"] = tx.tipo
    st.session_state["ed_valor"] = float(tx.valor)
    st.session_state["ed_data"] = tx.data
    st.session_state["confirmar_exclusao"] = False


# --------------------------------------------------------------------------
# Login
# --------------------------------------------------------------------------
def _pagina_login() -> None:
    _, card, _ = st.columns([1, 1.3, 1])
    with card:
        st.markdown("## 💳 FinControl")
        st.markdown("**Sistema Financeiro · Demonstração**")
        st.write("")
        with st.form("login"):
            usuario = st.text_input("Usuário", value=USUARIO_DEMO)
            senha = st.text_input("Senha", value="demo", type="password")
            enviado = st.form_submit_button("Entrar", width="stretch", type="primary")
            if enviado:
                if usuario.strip() and senha.strip():
                    st.session_state.usuario = usuario.strip()
                    st.session_state.logado = True
                    st.rerun()
                else:
                    st.error("Informe usuário e senha.")
        st.caption(
            "Modo demonstração: aceita qualquer usuário e senha. "
            "Nenhum dado é gravado em banco de dados real."
        )


# --------------------------------------------------------------------------
# Componentes de layout
# --------------------------------------------------------------------------
def _cabecalho(titulo: str, subtitulo: str) -> None:
    col_a, col_b = st.columns([4, 1], vertical_alignment="bottom")
    with col_a:
        st.title(titulo)
        st.caption(subtitulo)
    with col_b:
        st.markdown("<span class='demo-badge'>demo</span>", unsafe_allow_html=True)


def _sidebar() -> str:
    with st.sidebar:
        st.markdown("### 💳 FinControl")
        st.caption("Modo demonstração · dados fictícios")
        st.write("")
        pagina = st.radio(
            "Navegação", PAGINAS, label_visibility="collapsed", key="nav_pagina"
        )
        st.divider()
        with st.expander("Sobre esta demo"):
            st.write(
                "Versão demonstrativa independente do banco de dados real: "
                "os dados são fictícios e existem apenas nesta sessão. "
                "A versão contratada acrescenta cadastro real, persistência "
                "em SQLite e suíte de testes automatizados."
            )
        st.button("Sair", width="stretch", on_click=_sair)
        return pagina


# --------------------------------------------------------------------------
# Dashboard
# --------------------------------------------------------------------------
def _pagina_dashboard() -> None:
    lancamentos: list[Lancamento] = st.session_state.lancamentos
    if not lancamentos:
        st.info("Sem lançamentos ainda. Cadastre uma receita ou despesa.")
        return

    hoje = date.today()
    geral = totais(lancamentos)
    mes_atual = totais_do_mes(lancamentos, hoje)
    mes_passado = totais_do_mes(lancamentos, _mes_anterior(hoje))

    st.title(f"Olá, {st.session_state.usuario} 👋")
    st.caption("Aqui está o resumo das suas finanças.")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Saldo total", formatar_moeda(geral["saldo"]), border=True)

    dif_rec = mes_atual["receitas"] - mes_passado["receitas"]
    c2.metric(
        "Receitas no mês",
        formatar_moeda(mes_atual["receitas"]),
        delta=f"{formatar_moeda(abs(dif_rec))} vs. mês anterior",
        delta_color="normal",
        border=True,
    )

    dif_desp = mes_atual["despesas"] - mes_passado["despesas"]
    c3.metric(
        "Despesas no mês",
        formatar_moeda(mes_atual["despesas"]),
        delta=f"{formatar_moeda(abs(dif_desp))} vs. mês anterior",
        delta_color="inverse",
        border=True,
    )

    economia = f"{mes_atual['economia_pct']:.1f}".replace(".", ",") + " %"
    c4.metric("Taxa de economia (mês)", economia, border=True)

    st.write("")
    col_esq, col_dir = st.columns([3, 2], gap="large")

    with col_esq:
        st.subheader("Evolução do saldo")
        dados = pd.DataFrame(evolucao_saldo(lancamentos, meses=6))
        fig = px.area(dados, x="mes", y="saldo", markers=True)
        fig.update_traces(
            line_color="#4f8cff",
            fillcolor="rgba(79, 140, 255, 0.16)",
            hovertemplate="%{x}<br>R$ %{y:,.2f}<extra></extra>",
        )
        fig.update_layout(
            height=330,
            margin=dict(l=0, r=0, t=10, b=0),
            showlegend=False,
            xaxis_title="",
            yaxis_title="",
            yaxis=dict(tickprefix="R$ ", separatethousands=True),
            hovermode="x unified",
        )
        st.plotly_chart(fig)

    with col_dir:
        st.subheader("Despesas por categoria")
        categorias = despesas_por_categoria(lancamentos)
        df_cat = pd.DataFrame(
            {"Categoria": list(categorias), "Valor": list(categorias.values())}
        )
        fig_pizza = px.pie(
            df_cat,
            names="Categoria",
            values="Valor",
            hole=0.55,
            color_discrete_sequence=[
                "#4f8cff", "#12b886", "#f59f00", "#e8590c",
                "#7048e8", "#e64980", "#15aabf", "#868e96",
            ],
        )
        fig_pizza.update_traces(
            textposition="inside",
            textinfo="percent+label",
            textfont_size=11,
            hovertemplate="%{label}<br>R$ %{value:,.2f}<extra></extra>",
        )
        fig_pizza.update_layout(
            height=330,
            margin=dict(l=10, r=10, t=10, b=10),
            showlegend=False,
        )
        st.plotly_chart(fig_pizza)

    st.subheader("Metas em andamento")
    for meta in st.session_state.metas:
        prog = progresso_meta(meta)
        st.progress(
            prog,
            text=(
                f"**{meta.nome}** — {formatar_moeda(meta.valor_atual)} de "
                f"{formatar_moeda(meta.valor_alvo)} ({prog * 100:.0f}%)"
            ),
        )


# --------------------------------------------------------------------------
# Transacoes: tabela + nova + editar/excluir (padrao da referencia)
# --------------------------------------------------------------------------
def _pagina_transacoes() -> None:
    todas: list[Lancamento] = st.session_state.lancamentos
    resumo = totais(todas)
    _cabecalho(
        "Transações",
        f"{len(todas)} lançamentos · receitas {formatar_moeda(resumo['receitas'])}"
        f" · despesas {formatar_moeda(resumo['despesas'])}",
    )

    # ---- filtro ----
    filtro = st.radio(
        "Filtrar por tipo",
        ["Todas", "Receitas", "Despesas"],
        horizontal=True,
        key="filtro_tipo",
    )
    if filtro == "Receitas":
        lista = [l for l in todas if l.tipo == TIPO_RECEITA]
    elif filtro == "Despesas":
        lista = [l for l in todas if l.tipo == TIPO_DESPESA]
    else:
        lista = todas

    col_esq, col_dir = st.columns([3, 2], gap="large")

    # ---- tabela ----
    with col_esq:
        st.subheader("Lançamentos")
        if not lista:
            st.info("Nenhuma transação com esse filtro.")
        else:
            ordenado = sorted(lista, key=lambda l: (l.data, l.id), reverse=True)
            df = pd.DataFrame(
                [
                    {
                        "ID": l.id,
                        "Data": formatar_data(l.data),
                        "Tipo": l.tipo,
                        "Descrição": l.descricao,
                        "Categoria": l.categoria,
                        "Valor": formatar_moeda(l.valor),
                    }
                    for l in ordenado
                ]
            )
            st.dataframe(df, hide_index=True, height=440)

    # ---- nova transacao ----
    with col_dir:
        st.subheader("Nova transação")
        tipo_novo = st.selectbox(
            "Tipo", [TIPO_RECEITA, TIPO_DESPESA], key="nova_tipo"
        )
        with st.form("form_nova", clear_on_submit=True):
            descricao = st.text_input(
                "Descrição", placeholder="Ex.: Salário, Mercado, Uber..."
            )
            opcoes_cat = (
                CATEGORIAS_RECEITA if tipo_novo == TIPO_RECEITA else CATEGORIAS_DESPESA
            )
            categoria = st.selectbox("Categoria", opcoes_cat)
            valor = st.number_input(
                "Valor (R$)", min_value=0.0, step=0.01, format="%.2f"
            )
            data = st.date_input("Data", value=date.today())
            enviado = st.form_submit_button(
                "Salvar transação", width="stretch", type="primary"
            )
            if enviado:
                try:
                    validar_lancamento(descricao, valor, data)
                except ValueError as erro:
                    st.error(str(erro))
                else:
                    nova_tx = Lancamento(
                        id=_novo_id(),
                        tipo=tipo_novo,
                        descricao=descricao.strip(),
                        valor=round(float(valor), 2),
                        categoria=categoria,
                        data=data,
                    )
                    st.session_state.lancamentos.append(nova_tx)
                    st.session_state["_selecionar_id"] = nova_tx.id
                    st.toast(f"Transação salva: {descricao.strip()}")
                    st.rerun()

    # ---- editar ou excluir ----
    st.write("")
    st.subheader("Editar ou excluir transação")

    if not todas:
        st.info("Nenhuma transação cadastrada para editar.")
        return

    opcoes = [
        _opcao_de_transacao(l)
        for l in sorted(todas, key=lambda l: (l.data, l.id), reverse=True)
    ]

    # pos-criacao: foca a transacao recem-salva no seletor de edicao
    alvo_novo = st.session_state.pop("_selecionar_id", None)
    if alvo_novo is not None:
        tx_alvo = _por_id(todas, alvo_novo)
        if tx_alvo is not None:
            st.session_state["sel_transacao"] = _opcao_de_transacao(tx_alvo)

    # garante selecao valida antes de instanciar o widget
    if st.session_state.get("sel_transacao") not in opcoes:
        st.session_state["sel_transacao"] = opcoes[0]

    selecao = st.selectbox("Selecione pelo ID", opcoes, key="sel_transacao")

    atual = _por_id(todas, _id_da_opcao(selecao))
    if atual is None:  # defensivo: nunca deve acontecer
        st.session_state["sel_transacao"] = opcoes[0]
        atual = _por_id(todas, _id_da_opcao(opcoes[0]))
    if st.session_state.get("ed_id") != atual.id:
        _carregar_edicao(atual)

    st.text_input("Descrição", key="ed_descricao")
    cats_ed = (
        CATEGORIAS_RECEITA
        if st.session_state["ed_tipo"] == TIPO_RECEITA
        else CATEGORIAS_DESPESA
    )
    st.selectbox("Categoria", cats_ed, key="ed_categoria")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.selectbox("Tipo", [TIPO_RECEITA, TIPO_DESPESA], key="ed_tipo")
    with c2:
        st.number_input(
            "Valor (R$)", min_value=0.0, step=0.01, format="%.2f", key="ed_valor"
        )
    with c3:
        st.date_input("Data", key="ed_data")

    if st.button("Salvar alterações", key="btn_salvar_edicao", type="primary"):
        try:
            validar_lancamento(
                st.session_state["ed_descricao"],
                st.session_state["ed_valor"],
                st.session_state["ed_data"],
            )
        except ValueError as erro:
            st.error(str(erro))
        else:
            idx = next(
                i for i, l in enumerate(todas)
                if l.id == st.session_state["ed_id"]
            )
            st.session_state.lancamentos[idx] = substituir(
                todas[idx],
                descricao=st.session_state["ed_descricao"].strip(),
                valor=round(float(st.session_state["ed_valor"]), 2),
                categoria=st.session_state["ed_categoria"],
                tipo=st.session_state["ed_tipo"],
                data=st.session_state["ed_data"],
            )
            st.toast("Alterações salvas")
            st.rerun()

    st.write("")
    confirmado = st.checkbox(
        f"Confirmo a exclusão de {selecao}", key="confirmar_exclusao"
    )
    if st.button("Excluir transação", key="btn_excluir_tx", disabled=not confirmado):
        st.session_state.lancamentos = [
            l for l in st.session_state.lancamentos if l.id != atual.id
        ]
        st.toast("Transação excluída")
        st.rerun()


# --------------------------------------------------------------------------
# Metas
# --------------------------------------------------------------------------
def _pagina_metas() -> None:
    metas: list[Meta] = st.session_state.metas
    _cabecalho(
        "Metas financeiras",
        f"{len(metas)} metas ativas · acompanhe o progresso de cada objetivo",
    )

    if metas:
        colunas = st.columns(len(metas))
        for col, meta in zip(colunas, metas):
            with col.container(border=True):
                st.markdown(f"#### {meta.nome}")
                prog = progresso_meta(meta)
                st.progress(prog, text=f"{prog * 100:.0f}% concluído")
                st.caption(
                    f"Aplicado: **{formatar_moeda(meta.valor_atual)}** de "
                    f"{formatar_moeda(meta.valor_alvo)}"
                )
                restante = max(0.0, meta.valor_alvo - meta.valor_atual)
                st.caption(f"Faltam: {formatar_moeda(restante)}")
                if meta.prazo:
                    st.caption(f"Prazo: {formatar_data(meta.prazo)}")

        st.write("")
        st.subheader("Aportar em uma meta")
        with st.form("form_aporte", clear_on_submit=True):
            nomes = {m.nome: m.id for m in metas}
            escolhida = st.selectbox("Meta", list(nomes))
            valor = st.number_input(
                "Valor a aportar (R$)", min_value=0.0, step=0.01, format="%.2f"
            )
            enviado = st.form_submit_button("Aportar", width="stretch", type="primary")
            if enviado:
                if valor <= 0:
                    st.error("O valor deve ser maior que zero.")
                else:
                    alvo = next(m for m in metas if m.id == nomes[escolhida])
                    alvo.valor_atual = round(alvo.valor_atual + valor, 2)
                    st.toast(f"Aporte de {formatar_moeda(valor)} em {alvo.nome}")
                    st.rerun()

        st.write("")

    # criar nova meta (sempre disponivel, como na referencia)
    with st.expander("Criar nova meta"):
        with st.form("form_meta", clear_on_submit=True):
            nome = st.text_input(
                "Nome da meta", placeholder="Ex.: Reserva de emergência"
            )
            alvo = st.number_input(
                "Valor alvo (R$)", min_value=0.0, step=0.01, format="%.2f"
            )
            aplicado = st.number_input(
                "Já aplicado (R$)", min_value=0.0, step=0.01, format="%.2f"
            )
            prazo = st.date_input("Prazo", value=date(date.today().year + 1, 6, 30))
            enviado = st.form_submit_button("Criar meta", width="stretch", type="primary")
            if enviado:
                try:
                    nova = Meta(
                        id=_nova_id_meta(),
                        nome=nome,
                        valor_alvo=float(alvo),
                        valor_atual=float(aplicado),
                        prazo=prazo,
                    )
                except ValueError as erro:
                    st.error(str(erro))
                else:
                    st.session_state.metas.append(nova)
                    st.toast(f"Meta criada: {nova.nome}")
                    st.rerun()

    if not metas:
        st.info("Você ainda não tem metas financeiras cadastradas.")


# --------------------------------------------------------------------------
# Principal
# --------------------------------------------------------------------------
def main() -> None:
    _iniciar_estado()
    if not st.session_state.logado:
        _pagina_login()
        return
    pagina = _sidebar()
    if pagina == "Dashboard":
        _pagina_dashboard()
    elif pagina == "Transações":
        _pagina_transacoes()
    else:
        _pagina_metas()


if __name__ == "__main__":
    main()
