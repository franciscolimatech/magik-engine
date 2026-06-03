# MAGIK Engine

MAGIK Engine e uma base inicial em Python para apoiar sessoes de RPG de mesa.
Ele nao substitui o mestre: o objetivo e controlar fichas, dados, habilidades,
consequencias e historico da sessao.

## Requisitos

- Python 3.11+
- pytest para testes

## Como instalar em um clone limpo

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

## Como rodar

```powershell
python main.py
```

Se os arquivos em `data/` nao existirem, o MAGIK Engine cria automaticamente
`characters.json`, `sessions.json` e `world_state.json` com os dados iniciais.

O terminal mostra o menu:

```text
1 - Ver ficha do Miko
2 - Rolar dado
3 - Usar Roleta Sombria da Ikisaki
4 - Usar Cajado Sombrio
5 - Registrar acontecimento
6 - Ver historico
0 - Sair
```

## Como testar

```powershell
python -m pytest
```

## Estrutura

- `src/core`: modelos e regras centrais, como dados, personagem e sessoes.
- `src/systems`: sistemas especificos de jogo, como Ikisaki, maldicoes e Cajado Sombrio.
- `src/storage`: contratos e adaptadores de armazenamento JSON ou memoria.
- `src/ui`: entrada e saida da interface simples via terminal.
- `data`: arquivos JSON usados como armazenamento inicial.
- `tests`: testes basicos com pytest.

## Estado atual

Esta primeira versao inclui:

- Rolagem de dados no formato `1d20`, `1d10`, `2d6` etc.
- Ficha inicial do personagem Miko Meu.
- Roleta Sombria: Dez Elos de Ikisaki.
- Cajado Sombrio como alternativa quando Ikisaki estiver indisponivel.
- Registro e consulta de historico de sessao em `data/sessions.json`.

Nao ha integracao com IA nesta etapa.
