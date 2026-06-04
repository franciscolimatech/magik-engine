"""Safe AI/fallback interpreter for player-described special powers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from typing import Any, Callable

from src.ai.narrator import AIConfig, AIClient, OpenAIResponsesClient
from src.ai.ollama_client import generate_with_ollama, get_ollama_status


POWER_TYPES = {
    "ataque",
    "defesa",
    "suporte",
    "cura",
    "magia",
    "controle",
    "utilidade",
    "transformacao",
    "passiva",
    "unica",
}
DEFAULT_LIMITATION = "Exige aprovacao do mestre e pode ter custo narrativo."
DEFAULT_USAGE = "1 vez por cena ou conforme decisao do mestre."
MASTER_APPROVAL = "Sugestao nao oficial. O mestre deve aprovar antes de usar em jogo."


@dataclass(frozen=True)
class PowerInterpretation:
    source: str
    nome: str
    tipo: str
    descricao: str
    efeito_narrativo: str
    limitacao: str
    custo_ou_preco: str
    uso_sugerido: str
    teste_sugerido: str
    observacao_do_mestre: str
    deve_ser_aprovado: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def interpret_power(
    *,
    character_name: str,
    character_class: str,
    equipment: list[str] | None,
    raw_power: str,
    story: str = "",
    config: AIConfig | None = None,
    openai_client: AIClient | None = None,
    ollama_status_provider: Callable[[], dict[str, Any]] = get_ollama_status,
    ollama_generator: Callable[[str, str | None], str] = generate_with_ollama,
) -> dict[str, Any]:
    context = {
        "nome_personagem": character_name,
        "classe": character_class,
        "equipamentos": equipment or [],
        "poder_especial_bruto": raw_power,
        "personalidade_historia": story,
    }
    prompt = build_power_prompt(context)
    resolved_config = config or AIConfig.from_env()

    if not resolved_config.enabled:
        return fallback_power_interpretation(raw_power).to_dict()

    status = ollama_status_provider()
    if status.get("available"):
        try:
            text = ollama_generator(prompt, str(status.get("model") or ""))
            return _interpretation_from_ai_text(text, source="ollama", raw_power=raw_power).to_dict()
        except Exception:
            pass

    if resolved_config.api_key:
        try:
            text = (openai_client or OpenAIResponsesClient()).complete(prompt, resolved_config)
            return _interpretation_from_ai_text(text, source="openai", raw_power=raw_power).to_dict()
        except Exception:
            pass

    return fallback_power_interpretation(raw_power).to_dict()


def build_power_prompt(context: dict[str, Any]) -> str:
    safe_context = {
        "nome_personagem": str(context.get("nome_personagem", "")),
        "classe": str(context.get("classe", "")),
        "equipamentos": list(context.get("equipamentos") or []),
        "poder_especial_bruto": str(context.get("poder_especial_bruto", "")),
        "personalidade_historia": str(context.get("personalidade_historia", "")),
    }
    return "\n".join(
        [
            "Voce interpreta um poder especial de personagem para MAGIK Engine.",
            "Responda somente com JSON valido.",
            "Campos obrigatorios: nome, tipo, descricao, efeito_narrativo, limitacao, custo_ou_preco, uso_sugerido, teste_sugerido, observacao_do_mestre, deve_ser_aprovado.",
            "Guardrails: nao alterar vida, nao alterar armadura, nao criar dano fixo obrigatorio, nao criar invencibilidade, nao criar poder infinito, nao sobrescrever regra oficial, nao dizer que esta aprovado oficialmente.",
            "Sempre inclua aprovacao do mestre. Se o poder for absurdo, preserve o conceito e sugira limitacao clara.",
            json.dumps(safe_context, ensure_ascii=False),
        ]
    )


def fallback_power_interpretation(raw_power: str) -> PowerInterpretation:
    cleaned = raw_power.strip() or "Poder especial nao descrito."
    limitation = DEFAULT_LIMITATION
    if _looks_absurd(cleaned):
        limitation = (
            "Conceito muito forte: precisa ser limitado pelo mestre, ter alcance curto, custo narrativo "
            "e nunca garantir sucesso automatico."
        )
    return PowerInterpretation(
        source="fallback",
        nome="Poder Especial",
        tipo="utilidade",
        descricao=cleaned,
        efeito_narrativo=f"Permite tentar manifestar o conceito descrito: {cleaned}",
        limitacao=limitation,
        custo_ou_preco="Pode exigir esforco, risco narrativo ou consequencia definida pelo mestre.",
        uso_sugerido=DEFAULT_USAGE,
        teste_sugerido="Teste apropriado definido pelo mestre.",
        observacao_do_mestre=MASTER_APPROVAL,
        deve_ser_aprovado=True,
    )


def _interpretation_from_ai_text(text: str, source: str, raw_power: str) -> PowerInterpretation:
    try:
        data = json.loads(_extract_json(text))
    except (TypeError, ValueError, json.JSONDecodeError):
        return fallback_power_interpretation(raw_power)

    return _normalize_interpretation(data, source=source, raw_power=raw_power)


def _normalize_interpretation(data: dict[str, Any], source: str, raw_power: str) -> PowerInterpretation:
    fallback = fallback_power_interpretation(raw_power)
    tipo = str(data.get("tipo") or fallback.tipo).strip().casefold()
    if tipo not in POWER_TYPES:
        tipo = "utilidade"
    limitacao = _required_text(data.get("limitacao"), fallback.limitacao)
    if _looks_absurd(raw_power) and "mestre" not in limitacao.casefold():
        limitacao = f"{limitacao} Exige limitacao clara do mestre."
    observation = _required_text(data.get("observacao_do_mestre"), MASTER_APPROVAL)
    if "mestre" not in observation.casefold() or "apro" not in observation.casefold():
        observation = f"{observation} {MASTER_APPROVAL}"
    return PowerInterpretation(
        source=source,
        nome=_required_text(data.get("nome"), fallback.nome),
        tipo=tipo,
        descricao=_required_text(data.get("descricao"), fallback.descricao),
        efeito_narrativo=_required_text(data.get("efeito_narrativo"), fallback.efeito_narrativo),
        limitacao=limitacao,
        custo_ou_preco=_required_text(data.get("custo_ou_preco"), fallback.custo_ou_preco),
        uso_sugerido=_required_text(data.get("uso_sugerido"), fallback.uso_sugerido),
        teste_sugerido=_required_text(data.get("teste_sugerido"), fallback.teste_sugerido),
        observacao_do_mestre=observation,
        deve_ser_aprovado=True,
    )


def _extract_json(text: str) -> str:
    cleaned = text.strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end < start:
        return cleaned
    return cleaned[start : end + 1]


def _required_text(value: Any, fallback: str) -> str:
    text = str(value).strip() if value is not None else ""
    return text or fallback


def _looks_absurd(text: str) -> bool:
    normalized = text.casefold()
    red_flags = (
        "invencivel",
        "infinito",
        "mata qualquer",
        "sempre vence",
        "imortal",
        "dano infinito",
        "controlar tudo",
        "sem limite",
    )
    return any(flag in normalized for flag in red_flags)
