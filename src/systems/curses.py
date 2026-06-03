"""Simple consequence helpers for chain debts."""

from __future__ import annotations


def chain_debt_generates_switch_risk(chain_debts: int) -> bool:
    return chain_debts >= 3


def describe_chain_debt_risk(chain_debts: int) -> str:
    if chain_debts >= 3:
        return "Risco de Switch Sombrio ativo: as Dividas de Corrente chegaram a 3 ou mais."
    if chain_debts == 2:
        return "A corrente esta rangendo perto do limite."
    if chain_debts == 1:
        return "Uma Divida de Corrente foi marcada."
    return "Sem Dividas de Corrente no momento."
