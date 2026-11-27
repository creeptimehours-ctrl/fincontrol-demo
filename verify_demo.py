# verify_demo.py | Teste completo da demo via AppTest (sem navegador) | Python 3.11
from streamlit.testing.v1 import AppTest


def botao(at: AppTest, rotulo: str):
    """Localiza um botao pelo rotulo visivel."""
    return next(b for b in at.button if b.label == rotulo)


at = AppTest.from_file("app.py", default_timeout=60)
at.run()
assert not at.exception, f"login falhou: {at.exception}"
print("[1/9] tela de login: OK")

botao(at, "Entrar").click().run()
assert not at.exception, f"login submit falhou: {at.exception}"
assert at.session_state["logado"] is True, "sessao nao logou"
print("[2/9] autenticacao (modo demo): OK")

# ---- Dashboard ----
at.radio(key="nav_pagina").set_value("Dashboard").run()
assert not at.exception, f"dashboard falhou: {at.exception}"
assert len(at.metric) == 4, f"esperava 4 cards, veio {len(at.metric)}"
print("[3/9] Dashboard (4 cards + graficos): OK")

# ---- Transacoes ----
at.radio(key="nav_pagina").set_value("Transações").run()
assert not at.exception, f"transacoes falhou: {at.exception}"
assert len(at.dataframe) >= 1, "tabela de transacoes ausente"
n_inicial = len(at.session_state["lancamentos"])
print(f"[4/9] Transacoes (tabela com {n_inicial} lancamentos): OK")

# ---- Criar transacao ----
campo_desc = next(
    w for w in at.text_input if w.key is None and w.label == "Descrição"
)
campo_desc.set_value("Teste automatizado")
campo_valor = next(
    w for w in at.number_input if w.key is None and w.label == "Valor (R$)"
)
campo_valor.set_value(123.45)
botao(at, "Salvar transação").click().run()
assert not at.exception, f"criacao falhou: {at.exception}"
assert len(at.session_state["lancamentos"]) == n_inicial + 1, "nao criou a transacao"
print("[5/9] Criar transacao: OK")

# ---- Editar transacao (a recem-criada esta selecionada por padrao) ----
at.text_input(key="ed_descricao").set_value("Investimento editado")
botao(at, "Salvar alterações").click().run()
assert not at.exception, f"edicao falhou: {at.exception}"
assert (
    at.session_state["lancamentos"][-1].descricao == "Investimento editado"
), "edicao nao persistiu"
print("[6/9] Editar transacao: OK")

# ---- Excluir transacao (com confirmacao) ----
at.checkbox(key="confirmar_exclusao").set_value(True)
at.run()
assert not at.exception, f"checkbox falhou: {at.exception}"
botao(at, "Excluir transação").click().run()
assert not at.exception, f"exclusao falhou: {at.exception}"
assert len(at.session_state["lancamentos"]) == n_inicial, "exclusao nao removeu"
print("[7/9] Excluir transacao (com confirmacao): OK")

# ---- Metas ----
at.radio(key="nav_pagina").set_value("Metas").run()
assert not at.exception, f"metas falhou: {at.exception}"
assert len(at.session_state["metas"]) == 3, "metas da demo sumiram"
print("[8/9] Metas (3 metas + criar/aportar): OK")

# ---- Estado vazio das metas (como na referencia do cliente) ----
at.session_state["metas"] = []
at.run()
assert not at.exception, f"estado vazio falhou: {at.exception}"
print("[9/9] Metas em estado vazio (mensagem da referencia): OK")

print("SMOKE TEST PASSED - 9/9")
