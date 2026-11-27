# core.py | Regras de negócio puras do Sistema Financeiro - sem Streamlit, sem SQLite | Python 3.11
"""Núcleo do Sistema Financeiro.

Todas as funções são puras (entrada -> saída, sem efeitos colaterais)
para que a suite Pytest cubra a lógica sem depender de UI nem de banco.
Este módulo é a camada que permanece igual na demo e na versão final.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable, Optional

TIPO_RECEITA = "receita"
TIPO_DESPESA = "despesa"

CATEGORIAS_RECEITA = ["Salário", "Freela", "Investimentos", "Reembolso", "Geral"]
CATEGORIAS_DESPESA = [
    "Moradia",
    "Alimentação",
    "Transporte",
    "Saúde",
    "Educação",
    "Lazer",
    "Assinaturas",
    "Geral",
]

_MESES_ABR = (
    "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
    "Jul", "Ago", "Set", "Out", "Nov", "Dez",
)


@dataclass(frozen=True)
class Lancamento:
    """Registro financeiro imutável (receita ou despesa)."""

    id: int
    tipo: str
    descricao: str
    valor: float
    categoria: str
    data: date

    def __post_init__(self) -> None:
        if self.tipo not in (TIPO_RECEITA, TIPO_DESPESA):
            raise ValueError("Tipo inválido: use 'receita' ou 'despesa'.")
        validar_lancamento(self.descricao, self.valor, self.data)


@dataclass
class Meta:
    """Objetivo financeiro com valor alvo e progresso atual."""

    id: int
    nome: str
    valor_alvo: float
    valor_atual: float
    prazo: Optional[date] = None

    def __post_init__(self) -> None:
        if not str(self.nome).strip():
            raise ValueError("O nome da meta não pode ficar vazio.")
        if self.valor_alvo <= 0:
            raise ValueError("O valor alvo da meta deve ser maior que zero.")
        if self.valor_atual < 0:
            raise ValueError("O valor já aplicado não pode ser negativo.")


def validar_lancamento(descricao: str, valor: float, data: date) -> None:
    """Valida um lançamento. Lança ValueError com mensagem em português."""
    if not isinstance(descricao, str) or not descricao.strip():
        raise ValueError("A descrição não pode ficar vazia.")
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        raise ValueError("O valor precisa ser um número.") from None
    if numero <= 0:
        raise ValueError("O valor deve ser maior que zero.")
    if not isinstance(data, date):
        raise ValueError("Data inválida.")


def formatar_moeda(valor: float) -> str:
    """Converte 1234.5 -> 'R$ 1.234,50' (padrão pt-BR, sem depender de locale)."""
    texto = f"{float(valor):,.2f}"
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_data(data: date) -> str:
    """Converte date -> 'dd/mm/aaaa'."""
    return data.strftime("%d/%m/%Y")


def totais(lancamentos: Iterable[Lancamento]) -> dict:
    """Soma geral: receitas, despesas, saldo e taxa de economia (%)."""
    receitas = sum(l.valor for l in lancamentos if l.tipo == TIPO_RECEITA)
    despesas = sum(l.valor for l in lancamentos if l.tipo == TIPO_DESPESA)
    saldo = receitas - despesas
    economia = (saldo / receitas * 100.0) if receitas else 0.0
    return {
        "receitas": receitas,
        "despesas": despesas,
        "saldo": saldo,
        "economia_pct": economia,
    }


def totais_do_mes(
    lancamentos: Iterable[Lancamento], ref: Optional[date] = None
) -> dict:
    """Totais restritos ao mês de `ref` (padrão: mês corrente)."""
    ref = ref or date.today()
    do_mes = [
        l for l in lancamentos
        if l.data.year == ref.year and l.data.month == ref.month
    ]
    return totais(do_mes)


def evolucao_saldo(
    lancamentos: Iterable[Lancamento], meses: int = 6,
    ref: Optional[date] = None,
) -> list[dict]:
    """Saldo acumulado mês a mês, retornando os últimos `meses` pontos."""
    ref = ref or date.today()
    liquido: dict[tuple[int, int], float] = {}
    for l in lancamentos:
        chave = (l.data.year, l.data.month)
        delta = l.valor if l.tipo == TIPO_RECEITA else -l.valor
        liquido[chave] = liquido.get(chave, 0.0) + delta

    if not liquido:
        return []

    inicio = min(liquido)
    pontos: list[dict] = []
    acumulado = 0.0
    ano, mes = inicio
    while (ano, mes) <= (ref.year, ref.month):
        acumulado += liquido.get((ano, mes), 0.0)
        pontos.append(
            {"mes": f"{_MESES_ABR[mes - 1]}/{str(ano)[2:]}", "saldo": round(acumulado, 2)}
        )
        mes += 1
        if mes == 13:
            mes, ano = 1, ano + 1
    return pontos[-meses:]


def despesas_por_categoria(
    lancamentos: Iterable[Lancamento],
) -> dict[str, float]:
    """Total de despesas por categoria, do maior para o menor."""
    acumulado: dict[str, float] = {}
    for l in lancamentos:
        if l.tipo == TIPO_DESPESA:
            acumulado[l.categoria] = acumulado.get(l.categoria, 0.0) + l.valor
    return dict(sorted(acumulado.items(), key=lambda item: -item[1]))


def progresso_meta(meta: Meta) -> float:
    """Progresso da meta entre 0.0 e 1.0 (nunca estoura a barra)."""
    if meta.valor_alvo <= 0:
        return 0.0
    return max(0.0, min(1.0, meta.valor_atual / meta.valor_alvo))
