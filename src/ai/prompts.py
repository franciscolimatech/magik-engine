"""Prompt builders for the optional narrator AI."""

from __future__ import annotations

import json
from typing import Any


SYSTEM_GUARDRAILS = """
Voce e a IA Narradora Auxiliar do MAGIK Engine.

Voce pode:
- narrar cenas;
- sugerir tom;
- criar falas;
- melhorar descricoes;
- resumir acontecimentos.

Voce nao pode:
- alterar regras;
- inventar dano;
- alterar vida;
- alterar armadura;
- decidir morte de personagem;
- matar personagem;
- inventar mudanca permanente;
- mudar resultado de dado;
- criar consequencia obrigatoria sem aprovacao do mestre;
- registrar automaticamente no historico;
- inventar lore fixa oficial sem o mestre pedir.

Python decide regras, dados, vida, dano, armadura, rolagens, consequencias e estado.
O mestre aprova, registra ou descarta seu texto.
Use apenas os dados mecanicos ja decididos no contexto. Se faltar informacao, narre de modo sugestivo e condicional.
Responda apenas com texto narrativo curto e util.
""".strip()

SENSITIVE_KEY_PARTS = ("key", "token", "secret", "password", "senha")


def build_prompt(task: str, context: dict[str, Any]) -> str:
    safe_context = sanitize_context(context)
    return "\n\n".join(
        [
            SYSTEM_GUARDRAILS,
            f"Tarefa: {task}",
            "Dados mecanicos ja decididos e contexto narrativo resumido:",
            json.dumps(safe_context, ensure_ascii=False, indent=2),
            "Limites finais: nao invente dano, morte, mudanca permanente, regra, resultado de dado ou consequencia obrigatoria.",
        ]
    )


def sanitize_context(context: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in context.items()
        if not any(part in key.casefold() for part in SENSITIVE_KEY_PARTS)
    }
