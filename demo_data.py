# demo_data.py | Dados fictícios da versão demonstrativa - não toca no banco real | Python 3.11
"""Gera o histórico de exemplo usado pela demo.

Determinístico (semente fixa) para que toda execução mostre os mesmos
números — importante para gravar vídeo/screenshots da proposta.
"""

from __future__ import annotations

import calendar
import random
from datetime import date
from typing import Optional

from core import Lancamento, Meta

USUARIO_DEMO = "demo"
SENHA_DEMO = "demo"


def _data_ref(hoje: date, meses_atras: int, dia: int) -> date:
    """Data com `meses_atras` meses antes do mês atual, dia limitado ao
    dia de hoje quando o mês é o corrente (nada no futuro na demo)."""
    total = hoje.month - 1 - meses_atras
    ano = hoje.year + total // 12
    mes = total % 12 + 1
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    if (ano, mes) == (hoje.year, hoje.month):
        ultimo_dia = min(ultimo_dia, hoje.day)
    return date(ano, mes, min(dia, ultimo_dia))


def gerar_lancamentos(hoje: Optional[date] = None) -> list[Lancamento]:
    """~55 lançamentos realistas dos últimos 6 meses."""
    hoje = hoje or date.today()
    rng = random.Random(7)  # semente fixa = demo reproduzível
    lista: list[Lancamento] = []

    def add(tipo: str, descricao: str, valor: float, categoria: str,
            meses_atras: int, dia: int) -> None:
        lista.append(
            Lancamento(
                id=len(lista) + 1,
                tipo=tipo,
                descricao=descricao,
                valor=round(float(valor), 2),
                categoria=categoria,
                data=_data_ref(hoje, meses_atras, dia),
            )
        )

    # Recorrências mensais dos últimos 6 meses (0 = mês corrente)
    for atras in range(5, -1, -1):
        add("receita", "Salário mensal", 4500.00, "Salário", atras, 5)
        add("despesa", "Aluguel", 1600.00, "Moradia", atras, 10)
        add("despesa", "Plano de saúde", 389.90, "Saúde", atras, 8)
        add("despesa", "Academia", 119.00, "Saúde", atras, 6)
        add("despesa", "Internet + celular", 149.90, "Assinaturas", atras, 12)
        add("despesa", "Mercado", rng.randint(760, 1050), "Alimentação", atras, 15)
        add("despesa", "Transporte (Uber/metro)", rng.randint(180, 320),
            "Transporte", atras, 20)
        add("despesa", "Streaming (3 assinaturas)", 97.00, "Lazer", atras, 22)

    # Eventuais pontuais
    add("receita", "Freela - landing page cliente A", 1800.00, "Freela", 1, 22)
    add("receita", "Freela - automação de relatórios", 950.00, "Freela", 3, 27)
    add("receita", "Dividendos do fundo DI", 143.52, "Investimentos", 1, 10)
    add("receita", "Reembolso de despesas", 210.00, "Reembolso", 2, 18)
    add("despesa", "Curso de inglês (mensalidade)", 320.00, "Educação", 2, 14)
    add("despesa", "Jantar de aniversário", 178.40, "Lazer", 1, 19)
    add("despesa", "Presente de aniversário", 260.00, "Geral", 2, 9)
    add("despesa", "Farmácia", 89.90, "Saúde", 3, 11)
    add("despesa", "Manutenção do carro", 640.00, "Transporte", 4, 17)
    add("despesa", "Assinatura de nuvem (2 TB)", 49.90, "Assinaturas", 4, 3)

    return lista


def gerar_metas(hoje: Optional[date] = None) -> list[Meta]:
    """Metas de exemplo com progressos coerentes com o histórico acima."""
    hoje = hoje or date.today()
    return [
        Meta(1, "Reserva de emergência", 18000.00, 11450.00,
             date(hoje.year + 1, 3, 31)),
        Meta(2, "Viagem das férias", 6000.00, 2550.00,
             date(hoje.year, 12, 20)),
        Meta(3, "Notebook novo", 5500.00, 4890.00,
             date(hoje.year + 1, 6, 30)),
    ]
