# MAGIK Engine

MAGIK Engine é uma ferramenta em Python para apoiar partidas de RPG de mesa.
O projeto reúne terminal interativo, interface web inicial, protótipo 2D,
campanhas, personagens, combates, histórico e uma IA narradora opcional.

Ele é um projeto pessoal, feito por lazer para jogar com amigos, e ainda está
em desenvolvimento.

## Status do Projeto

O MAGIK Engine já possui uma base funcional, mas ainda não é um produto final.
A proposta é evoluir o sistema aos poucos, mantendo o foco em uso real durante
sessões de RPG e também em aprendizado técnico.

Hoje o projeto pode ser considerado um protótipo avançado/MVP pessoal.

## Filosofia

O MAGIK Engine não substitui o mestre.

O sistema ajuda a organizar a mesa, controlar dados e registrar acontecimentos,
mas as decisões narrativas continuam sendo humanas. A regra principal é:

- Python controla regras, dados, vida, dano, armadura, rolagens e estado.
- A IA apenas sugere, narra ou melhora textos.
- O mestre aprova, adapta, registra ou descarta qualquer sugestão.

## Funcionalidades

### Terminal Interativo

- Menu principal para uso durante a mesa.
- Gerenciamento de personagens, criaturas, NPCs, combates, campanhas e sessões.
- Rolagem de dados, testes, dano físico, dano mágico, cura e histórico.
- Acesso aos sistemas especiais do Miko Meu, como Ikisaki e Cajado Sombrio.

### Interface Web com FastAPI/Jinja2

- Listagem de personagens.
- Criação visual de personagem com preview antes de salvar.
- Ficha visual.
- Edição de dados gerais, equipamentos, status e habilidades.

A interface web ainda é parcial e deve crescer nas próximas versões.

### Protótipo 2D com PyGame

- Menu inicial.
- Criador de personagem dentro do jogo.
- Aparência básica com sprites gerados por código.
- Mapa em tiles, câmera, HUD, NPCs, diálogos, escolhas e eventos.
- Encontros com criaturas e tela inicial de combate visual.

O jogo 2D é experimental e não substitui o terminal nem a web.

### Personagens e Habilidades

- Suporte a múltiplos personagens.
- Miko Meu como personagem inicial e exemplo.
- Habilidades gerais com tipo, uso, efeito, custo, limite e usos restantes.
- Sistemas especiais continuam separados das regras gerais.

### Criaturas e NPCs

- Criaturas/inimigos separados de personagens jogadores.
- NPCs com papel, atitude, rumores, status e observações.
- Base pronta para evoluir NPCs importantes com mais personalidade.

### Combates

- Regras de dano físico com armadura separada da vida.
- Dano mágico ignorando armadura.
- Cura limitada pela vida máxima.
- Organizador de combate por turnos com iniciativa, rodada, participantes e histórico.
- Combate visual inicial no PyGame.

### Campanhas e Sessões

- Campanhas com personagens, NPCs, locais importantes, eventos e pendências.
- Sessões com resumo, participantes, eventos, combates, recompensas e consequências.
- Integração parcial com o histórico geral.

### Histórico

- Registro cronológico de acontecimentos.
- Possibilidade de associar eventos a campanhas e sessões.
- Uso por terminal e integração experimental com o jogo 2D.

### Motor Narrativo

- Geração local de falas, eventos, rumores, presságios e consequências.
- Controle de tom narrativo.
- Fallback sem IA externa.

### IA Opcional

- Suporte a Ollama local.
- Suporte opcional à OpenAI API.
- Fallback local quando não houver IA configurada.
- Guardrails para impedir que a IA controle regras ou altere estado do jogo.

### Armazenamento JSON

- Dados persistidos inicialmente em arquivos JSON dentro de `data/`.
- Estrutura simples, fácil de inspecionar e adequada para prototipagem.

### Testes Automatizados

- Suíte de testes com `pytest`.
- Cobertura para core, sistemas, terminal, web, IA e jogo 2D.

## Tecnologias

- Python
- FastAPI
- Jinja2
- PyGame/PyGame-CE
- JSON
- Pytest
- Ollama opcional
- OpenAI SDK opcional

## Instalação

No PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

## Como Rodar

### Terminal

```powershell
python main.py
```

### Interface Web

```powershell
python -m uvicorn src.web.app:app --reload
```

Acesse:

```text
http://127.0.0.1:8000
```

### Game 2D

```powershell
python -m src.game.app
```

### Testes

```powershell
python -m pytest
```

## IA Opcional

O projeto funciona normalmente sem IA externa.

A ordem de uso é:

1. Ollama local, se disponível.
2. OpenAI API, se `OPENAI_API_KEY` existir.
3. Fallback local sem IA.

Para usar Ollama local:

```powershell
ollama pull llama3.2:3b
ollama run llama3.2:3b
```

Para usar OpenAI API:

```powershell
$env:OPENAI_API_KEY="sua-chave"
```

Chaves de API nunca devem ser colocadas no código, em JSONs ou em commits.
Use variáveis de ambiente e mantenha `.env` fora do versionamento.

## Estrutura do Projeto

```text
MAGIK Engine
|-- main.py
|-- data/
|-- src/
|   |-- core/
|   |-- systems/
|   |-- storage/
|   |-- ui/
|   |-- web/
|   |-- game/
|   `-- ai/
`-- tests/
```

Responsabilidades principais:

- `src/core`: modelos e regras centrais.
- `src/systems`: sistemas específicos de jogo e narrativa.
- `src/storage`: armazenamento JSON e memória para testes.
- `src/ui`: interface de terminal.
- `src/web`: aplicação FastAPI, rotas, templates e CSS.
- `src/game`: protótipo 2D em PyGame.
- `src/ai`: IA narradora, prompts, Ollama/OpenAI e fallback.
- `data`: arquivos JSON usados como armazenamento inicial.
- `tests`: testes automatizados.

## Roadmap

Próximos passos planejados:

- Melhorar a interface web de campanhas e sessões.
- Criar uma timeline mais útil para o histórico.
- Estruturar NPCs importantes com personalidade e memória narrativa.
- Melhorar validações e schemas dos arquivos JSON.
- Estudar importação de PDF como contexto opcional.
- Manter a IA sempre como auxiliar, nunca como dona das regras.

## Limitações Conhecidas

- JSON ainda é usado como armazenamento inicial.
- A interface web ainda é parcial.
- O protótipo 2D ainda é experimental.
- A IA não deve alterar regras, vida, dano, armadura, dados ou estado diretamente.
- Algumas áreas ainda precisam de polimento para uso contínuo em campanha longa.

## Inspiração

O MAGIK Engine se inspira em ferramentas de apoio a RPG com IA local/offline,
histórico persistente e organização de campanhas. A inspiração é conceitual:
o projeto não copia código de terceiros e mantém sua própria filosofia de
preservar o mestre humano no controle da mesa.

