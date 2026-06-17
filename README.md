# MAGIK Engine

MAGIK Engine é um projeto pessoal feito por lazer para apoiar partidas de RPG
de mesa com amigos. Ele ainda está em produção e muda com frequência conforme
novas ideias aparecem durante o desenvolvimento.

A ideia principal é simples: o sistema ajuda a controlar fichas, dados,
habilidades, criaturas, NPCs, combates, campanhas, histórico e algumas cenas
visuais em 2D, mas não substitui o mestre. As decisões narrativas, regras finais
da mesa e aprovação de consequências continuam sendo humanas.

## Status

Projeto em desenvolvimento.

Já existe uma base funcional com:

- terminal interativo;
- interface web inicial com FastAPI e Jinja2;
- protótipo 2D experimental em PyGame;
- personagens gerais, com Miko Meu como personagem inicial;
- habilidades gerais;
- sistemas especiais do Miko, como Ikisaki e Cajado Sombrio;
- criaturas, inimigos e NPCs;
- combate básico e combate por turnos;
- campanhas e sessões organizadas;
- histórico geral;
- motor narrativo sem IA;
- IA narradora opcional com fallback local;
- interpretação segura de poder especial no criador do jogo;
- sprites simples gerados por código.

Ainda não é uma versão final. O objetivo é evoluir aos poucos até virar uma
ferramenta gostosa de usar em mesa.

## Requisitos

- Python 3.11+
- pip
- pytest para testes

As dependências principais estão em `requirements.txt`, incluindo FastAPI,
Jinja2, PyGame/PyGame-CE, OpenAI SDK opcional e ferramentas de teste.

## Instalação

No PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

Os arquivos JSON em `data/` são usados como armazenamento inicial. Quando algum
arquivo esperado não existe ou está vazio, o projeto tenta criá-lo com uma base
segura.

## Rodar Pelo Terminal

```powershell
python main.py
```

O terminal é a interface mais completa do projeto. Ele permite gerenciar
personagens, criaturas, NPCs, combates, campanhas, sessões, histórico, testes,
dano, cura, narrativas e IA auxiliar.

Opções principais:

- `1`: ver ficha do Miko Meu como atalho;
- `3` e `4`: sistemas especiais do Miko, Ikisaki e Cajado Sombrio;
- `5` e `6`: registrar e consultar histórico;
- `7`, `8`, `9` e `18`: testes, dano físico, dano mágico e cura;
- `17`: gerenciar personagens;
- `20`: gerenciar criaturas e inimigos;
- `21`: gerenciar NPCs;
- `22`: gerenciar combates;
- `23`: gerenciar campanhas e sessões;
- `24`: IA Narradora Auxiliar.

## Rodar a Interface Web

```powershell
python -m uvicorn src.web.app:app --reload
```

Depois acesse:

```text
http://127.0.0.1:8000
```

A interface web ainda é inicial, mas já permite:

- listar personagens;
- criar personagens com formulário visual;
- revisar antes de salvar;
- abrir ficha visual;
- editar dados gerais;
- editar equipamentos, status e habilidades.

A web usa os módulos do `src/core`; a regra de negócio não deve ser duplicada
nas rotas ou templates.

## Rodar o Jogo 2D Experimental

```powershell
python -m src.game.app
```

O jogo 2D é uma camada visual experimental inspirada em RPGs retrô de grid. Ele
não substitui o terminal nem a web.

Controles:

- `WASD` ou setas: mover;
- `E` ou `Espaço`: interagir;
- `Enter`, `E` ou `Espaço`: avançar ou fechar diálogos;
- cima/baixo ou `W`/`S`: navegar escolhas e menus;
- `ESC`: voltar, fugir ou sair, dependendo da tela.

O protótipo 2D já possui:

- menu inicial;
- criador completo de personagem;
- escolha básica de aparência;
- sprites gerados por código;
- mapa em tiles;
- câmera;
- HUD;
- NPCs com diálogos e escolhas;
- eventos de mapa;
- encontros com criaturas;
- tela inicial de combate visual;
- integração experimental com campanhas e sessões.

O combate visual ainda é limitado. Ele usa regras do core quando possível, mas o
dano da batalha visual pode ser temporário na execução do jogo.

### Contexto do Jogo 2D

O jogo pode receber personagem, campanha e sessão por variáveis de ambiente:

```powershell
$env:MAGIK_GAME_CHARACTER_ID="miko-meu"
$env:MAGIK_GAME_CAMPAIGN_ID="id-da-campanha"
$env:MAGIK_GAME_SESSION_ID="id-da-sessao"
python -m src.game.app
```

Sem essas variáveis, o jogo usa Miko Meu ou um fallback seguro.

Para smoke test sem deixar a janela aberta:

```powershell
$env:MAGIK_GAME_MAX_FRAMES="3"
python -m src.game.app
Remove-Item Env:\MAGIK_GAME_MAX_FRAMES
```

## IA Narradora Auxiliar

A IA é opcional. O projeto deve continuar funcionando sem chave e sem serviço
local.

Regra principal:

- Python decide dados, dano, vida, armadura, rolagens e estado.
- IA apenas narra, sugere e organiza texto.
- O mestre aprova, registra ou descarta.

A ordem de uso é:

1. Ollama local, se disponível;
2. OpenAI API, se `OPENAI_API_KEY` existir;
3. fallback local sem IA.

Para Ollama:

```powershell
ollama pull llama3.2:3b
ollama run llama3.2:3b
```

Opcionalmente:

```powershell
$env:OLLAMA_MODEL="llama3.2:3b"
```

Para OpenAI:

```powershell
$env:OPENAI_API_KEY="sua-chave"
```

Nunca coloque chaves no código, em JSON ou em commits. O projeto inclui `.env`
e `.env.local` no `.gitignore`.

## Dados

O projeto usa JSON como armazenamento inicial:

- `data/characters.json`
- `data/creatures.json`
- `data/npcs.json`
- `data/sessions.json`
- `data/combats.json`
- `data/campaigns.json`
- `data/campaign_sessions.json`
- `data/world_state.json`

Esse formato é simples de inspecionar e bom para protótipo. No futuro, pode ser
substituído ou complementado por outro armazenamento.

## Estrutura do Projeto

```text
MAGIK Engine
|-- main.py
|-- data/
|-- src/
|   |-- ai/
|   |-- core/
|   |-- game/
|   |-- storage/
|   |-- systems/
|   |-- ui/
|   `-- web/
`-- tests/
```

Responsabilidades:

- `src/core`: regras e modelos principais;
- `src/systems`: sistemas específicos de jogo, como Ikisaki, Cajado e narrativa;
- `src/storage`: armazenamento JSON e memória para testes;
- `src/ui`: terminal;
- `src/web`: FastAPI, rotas, templates e CSS;
- `src/game`: protótipo 2D em PyGame;
- `src/ai`: narradora auxiliar, prompts, Ollama/OpenAI e fallback;
- `tests`: testes automatizados.

## Principais Sistemas

### Personagens

O sistema suporta múltiplos personagens. Miko Meu continua como personagem
inicial e exemplo, mas não é o único personagem possível.

Personagens podem ter:

- nome e classe;
- vida máxima e atual;
- armadura;
- equipamentos;
- habilidades;
- status;
- tags;
- observações;
- sistemas especiais.

### Habilidades

Habilidades gerais podem ser adicionadas a qualquer personagem. Elas registram
nome, tipo, uso, efeito, custo, limite de uso, usos restantes, teste sugerido e
observações.

Ikisaki e Cajado Sombrio aparecem na ficha do Miko, mas continuam tendo seus
próprios sistemas especiais.

### Criaturas e NPCs

Criaturas e inimigos são separados de personagens jogadores e podem receber
dano, cura, status e observações.

NPCs são entidades narrativas e sociais, com papel, atitude, rumores, status e
observações.

### Combate

O core possui regras para:

- dano físico com armadura separada da vida;
- dano mágico ignorando armadura;
- cura limitada pela vida máxima;
- dado de dano oficial baseado na vida atual.

Também existe um organizador de combate por turnos com iniciativa, rodadas,
participantes, histórico e sincronização segura quando possível.

### Campanhas e Sessões

Campanhas organizam o panorama da aventura. Sessões registram acontecimentos de
cada encontro de jogo, incluindo eventos, combates, recompensas, consequências,
pendências e observações.

O histórico geral continua existindo para registros livres e pode ser vinculado
a campanha/sessão.

### Motor Narrativo

O motor narrativo sem IA gera:

- falas da Ikisaki;
- consequências narrativas;
- eventos aleatórios;
- rumores;
- presságios.

Ele aceita tons como `neutro`, `sombrio`, `engraçado`, `perigoso` e
`misterioso`, e pode usar tipo de local como contexto sem inventar lore oficial.

## Testes

Rode:

```powershell
python -m pytest
```

Validações úteis:

```powershell
"0" | python main.py
$env:MAGIK_GAME_MAX_FRAMES="3"; python -m src.game.app; Remove-Item Env:\MAGIK_GAME_MAX_FRAMES
```

## Filosofia do Projeto

MAGIK Engine existe para deixar a mesa mais fluida, não para tirar controle do
mestre. Ele pode lembrar regras, organizar dados e sugerir texto, mas a história
continua pertencendo ao grupo.

É um projeto de lazer, feito para aprender, experimentar e preparar futuras
sessões com amigos.

