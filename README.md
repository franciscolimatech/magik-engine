# MAGIK Engine

MAGIK Engine é um projeto pessoal feito por lazer para apoiar partidas de RPG
de mesa com amigos. Ele ainda está em produção e muda com frequência conforme
novas ideias aparecem durante o desenvolvimento.

A ideia principal é simples: o sistema ajuda a controlar fichas, dados,
habilidades, criaturas, NPCs, combates, campanhas, histórico e algumas cenas
visuais em 2D, mas não substitui o mestre. As decisoes narrativas, regras finais
da mesa e aprovacão de consequências continuam sendo humanas.

## Status

Projeto em desenvolvimento.

Ja existe uma base funcional com:

- terminal interativo;
- interface web inicial com FastAPI e Jinja2;
- prototipo 2D experimental em PyGame;
- personagens gerais, com Miko Meu como personagem inicial;
- habilidades gerais;
- sistemas especiais do Miko, como Ikisaki e Cajado Sombrio;
- criaturas, inimigos e NPCs;
- combate basico e combate por turnos;
- campanhas e sessoes organizadas;
- historico geral;
- motor narrativo sem IA;
- IA narradora opcional com fallback local;
- interpretacao segura de poder especial no criador do jogo;
- sprites simples gerados por codigo.

Ainda nao e uma versao final. O objetivo e evoluir aos poucos ate virar uma
ferramenta gostosa de usar em mesa.

## Requisitos

- Python 3.11+
- pip
- pytest para testes

As dependencias principais estao em `requirements.txt`, incluindo FastAPI,
Jinja2, PyGame/PyGame-CE, OpenAI SDK opcional e ferramentas de teste.

## Instalacao

No PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

Os arquivos JSON em `data/` sao usados como armazenamento inicial. Quando algum
arquivo esperado nao existe ou esta vazio, o projeto tenta cria-lo com uma base
segura.

## Rodar Pelo Terminal

```powershell
python main.py
```

O terminal e a interface mais completa do projeto. Ele permite gerenciar
personagens, criaturas, NPCs, combates, campanhas, sessoes, historico, testes,
dano, cura, narrativas e IA auxiliar.

Opcoes principais:

- `1`: ver ficha do Miko Meu como atalho;
- `3` e `4`: sistemas especiais do Miko, Ikisaki e Cajado Sombrio;
- `5` e `6`: registrar e consultar historico;
- `7`, `8`, `9` e `18`: testes, dano fisico, dano magico e cura;
- `17`: gerenciar personagens;
- `20`: gerenciar criaturas e inimigos;
- `21`: gerenciar NPCs;
- `22`: gerenciar combates;
- `23`: gerenciar campanhas e sessoes;
- `24`: IA Narradora Auxiliar.

## Rodar a Interface Web

```powershell
python -m uvicorn src.web.app:app --reload
```

Depois acesse:

```text
http://127.0.0.1:8000
```

A interface web ainda e inicial, mas ja permite:

- listar personagens;
- criar personagens com formulario visual;
- revisar antes de salvar;
- abrir ficha visual;
- editar dados gerais;
- editar equipamentos, status e habilidades.

A web usa os modulos do `src/core`; a regra de negocio nao deve ser duplicada
nas rotas ou templates.

## Rodar o Jogo 2D Experimental

```powershell
python -m src.game.app
```

O jogo 2D e uma camada visual experimental inspirada em RPGs retro de grid. Ele
nao substitui o terminal nem a web.

Controles:

- `WASD` ou setas: mover;
- `E` ou `Espaco`: interagir;
- `Enter`, `E` ou `Espaco`: avancar ou fechar dialogos;
- cima/baixo ou `W`/`S`: navegar escolhas e menus;
- `ESC`: voltar, fugir ou sair, dependendo da tela.

O prototipo 2D ja possui:

- menu inicial;
- criador completo de personagem;
- escolha basica de aparencia;
- sprites gerados por codigo;
- mapa em tiles;
- camera;
- HUD;
- NPCs com dialogos e escolhas;
- eventos de mapa;
- encontros com criaturas;
- tela inicial de combate visual;
- integracao experimental com campanhas e sessoes.

O combate visual ainda e limitado. Ele usa regras do core quando possivel, mas o
dano da batalha visual pode ser temporario na execucao do jogo.

### Contexto do jogo 2D

O jogo pode receber personagem, campanha e sessao por variaveis de ambiente:

```powershell
$env:MAGIK_GAME_CHARACTER_ID="miko-meu"
$env:MAGIK_GAME_CAMPAIGN_ID="id-da-campanha"
$env:MAGIK_GAME_SESSION_ID="id-da-sessao"
python -m src.game.app
```

Sem essas variaveis, o jogo usa Miko Meu ou um fallback seguro.

Para smoke test sem deixar a janela aberta:

```powershell
$env:MAGIK_GAME_MAX_FRAMES="3"
python -m src.game.app
Remove-Item Env:\MAGIK_GAME_MAX_FRAMES
```

## IA Narradora Auxiliar

A IA e opcional. O projeto deve continuar funcionando sem chave e sem servico
local.

Regra principal:

- Python decide dados, dano, vida, armadura, rolagens e estado.
- IA apenas narra, sugere e organiza texto.
- O mestre aprova, registra ou descarta.

A ordem de uso e:

1. Ollama local, se disponivel;
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

Nunca coloque chaves no codigo, em JSON ou em commits. O projeto inclui `.env`
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

Esse formato e simples de inspecionar e bom para prototipo. No futuro, pode ser
substituido ou complementado por outro armazenamento.

## Estrutura do Projeto

```text
MAGIK Engine
├── main.py
├── data/
├── src/
│   ├── ai/
│   ├── core/
│   ├── game/
│   ├── storage/
│   ├── systems/
│   ├── ui/
│   └── web/
└── tests/
```

Responsabilidades:

- `src/core`: regras e modelos principais;
- `src/systems`: sistemas especificos de jogo, como Ikisaki, Cajado e narrativa;
- `src/storage`: armazenamento JSON e memoria para testes;
- `src/ui`: terminal;
- `src/web`: FastAPI, rotas, templates e CSS;
- `src/game`: prototipo 2D em PyGame;
- `src/ai`: narradora auxiliar, prompts, Ollama/OpenAI e fallback;
- `tests`: testes automatizados.

## Principais Sistemas

### Personagens

O sistema suporta multiplos personagens. Miko Meu continua como personagem
inicial e exemplo, mas nao e o unico personagem possivel.

Personagens podem ter:

- nome e classe;
- vida maxima e atual;
- armadura;
- equipamentos;
- habilidades;
- status;
- tags;
- observacoes;
- sistemas especiais.

### Habilidades

Habilidades gerais podem ser adicionadas a qualquer personagem. Elas registram
nome, tipo, uso, efeito, custo, limite de uso, usos restantes, teste sugerido e
observacoes.

Ikisaki e Cajado Sombrio aparecem na ficha do Miko, mas continuam tendo seus
proprios sistemas especiais.

### Criaturas e NPCs

Criaturas e inimigos sao separados de personagens jogadores e podem receber
dano, cura, status e observacoes.

NPCs sao entidades narrativas e sociais, com papel, atitude, rumores, status e
observacoes.

### Combate

O core possui regras para:

- dano fisico com armadura separada da vida;
- dano magico ignorando armadura;
- cura limitada pela vida maxima;
- dado de dano oficial baseado na vida atual.

Tambem existe um organizador de combate por turnos com iniciativa, rodadas,
participantes, historico e sincronizacao segura quando possivel.

### Campanhas e Sessoes

Campanhas organizam o panorama da aventura. Sessoes registram acontecimentos de
cada encontro de jogo, incluindo eventos, combates, recompensas, consequencias,
pendencias e observacoes.

O historico geral continua existindo para registros livres e pode ser vinculado
a campanha/sessao.

### Motor Narrativo

O motor narrativo sem IA gera:

- falas da Ikisaki;
- consequencias narrativas;
- eventos aleatorios;
- rumores;
- pressagios.

Ele aceita tons como `neutro`, `sombrio`, `engracado`, `perigoso` e
`misterioso`, e pode usar tipo de local como contexto sem inventar lore oficial.

## Testes

Rode:

```powershell
python -m pytest
```

Validacoes uteis:

```powershell
"0" | python main.py
$env:MAGIK_GAME_MAX_FRAMES="3"; python -m src.game.app; Remove-Item Env:\MAGIK_GAME_MAX_FRAMES
```

## Filosofia do Projeto

MAGIK Engine existe para deixar a mesa mais fluida, nao para tirar controle do
mestre. Ele pode lembrar regras, organizar dados e sugerir texto, mas a historia
continua pertencendo ao grupo.

E um projeto de lazer, feito para aprender, experimentar e preparar futuras
sessoes com amigos.

