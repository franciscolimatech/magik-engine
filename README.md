# MAGIK Engine

MAGIK Engine e uma base inicial em Python para apoiar sessoes de RPG de mesa.
Ele nao substitui o mestre: o objetivo e controlar fichas, dados, habilidades,
consequencias, regras mecanicas oficiais e historico da sessao. A decisao final
continua sendo do mestre.

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

## Interface web

A v0.9 adiciona uma base web com FastAPI, Jinja2 e CSS proprio, sem remover o
terminal. A interface usa os mesmos modulos de `core`, `systems` e `storage`;
as regras continuam no Python.

Instale as dependencias:

```powershell
pip install -r requirements.txt
```

Rode localmente:

```powershell
uvicorn src.web.app:app --reload
```

Acesse:

```text
http://127.0.0.1:8000
```

Na v0.9.2, a tela inicial traz atalhos e o modulo de personagens permite
listar fichas em cards visuais, abrir uma ficha com visual de RPG e criar
personagem com um criador visual completo. O formulario `/characters/new`
separa identidade, atributos, equipamentos, ate 3 habilidades iniciais e campos
de historia e interpretacao. Antes de salvar, `/characters/preview` mostra uma
revisao da ficha montada; a gravacao so acontece quando voce confirma.

A ficha `/characters/{id}` mostra cabecalho com nome, classe, tags e sistemas
especiais, barras visuais de vida e armadura, equipamentos em chips,
habilidades em cards e blocos de historia, personalidade, frases marcantes e
observacoes.

Na v0.9.3, a web tambem permite editar personagens sem passar pelo terminal.
Use `Editar personagem` na ficha para alterar nome, classe, vida, armadura,
tags, equipamentos, status e observacoes. Use `Editar habilidades` para listar,
adicionar, editar, remover e restaurar usos de habilidades gerais do
personagem. Essas telas continuam usando os modelos e validacoes do `src/core`.

As habilidades iniciais usam o sistema geral de habilidades do `src/core`, com
tipo, uso, efeito, custo, limite de uso, teste sugerido e observacoes. Campos de
habilidade completamente vazios sao ignorados. Campanhas, combates e IA
Narradora aparecem como areas futuras da interface web.

## Jogo 2D experimental

A v1.3 mantem o prototipo visual em PyGame inspirado em RPGs retro de grid,
sem remover nem substituir terminal ou web. Por enquanto ele e apenas uma
camada visual jogavel: nao implementa combate visual, nao usa IA e nao salva
alteracoes no estado do jogo.

Instale as dependencias com:

```powershell
python -m pip install -r requirements.txt
```

Rode o prototipo com:

```powershell
python -m src.game.app
```

Controles:

- `WASD` ou setas: mover em tiles.
- `E` ou `Espaco`: interagir com NPC no tile a frente do personagem.
- `Enter`, `E` ou `Espaco`: fechar dialogo.
- `ESC`: sair.

O mapa de teste agora e maior que a tela. Uma camera simples segue o player,
converte coordenadas do mundo para a tela e evita mostrar area fora do mapa.
O HUD exibe nome do personagem, nome do mapa e uma dica curta dos controles.
Os sprites ainda sao gerados por codigo com `pygame.Surface`: player por
direcao, NPC, tiles de chao, grama, parede, agua e marcador de interacao. Eles
servem como visual retro temporario, nao como assets finais.
Na v1.4, NPCs podem ter dialogos com multiplas falas, avancados com
`Espaco`, `Enter` ou `E`. O mapa tambem possui eventos simples por posicao,
como mensagens, pressagios e sinais narrativos. Eventos unicos disparam uma vez
durante a execucao; eventos repetiveis podem aparecer novamente. Nada disso e
salvo no historico ainda.

O jogo carrega o nome do Miko Meu de `data/characters.json` apenas para exibir
no canto da tela. Se Miko nao existir, mostra `Aventureiro`. Nenhum personagem e
alterado ou salvo pelo prototipo.

O terminal mostra o menu:

```text
1 - Ver ficha do Miko
2 - Rolar dado
3 - Usar Roleta Sombria da Ikisaki
4 - Usar Cajado Sombrio
5 - Registrar acontecimento
6 - Ver historico
7 - Realizar teste 1d20
8 - Simular dano fisico
9 - Simular dano magico
10 - Ver/organizar moeda Pedralume
11 - Ver locais conhecidos do mundo
12 - Gerar fala da Ikisaki
13 - Gerar consequencia narrativa
14 - Gerar evento aleatorio
15 - Gerar rumor
16 - Gerar pressagio da maldicao
17 - Gerenciar personagens
18 - Curar personagem
19 - Roteiro de teste manual
20 - Gerenciar criaturas/inimigos
21 - Gerenciar NPCs
22 - Gerenciar combates
23 - Gerenciar campanhas e sessoes
24 - IA Narradora Auxiliar
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
- `src/web`: aplicacao FastAPI, rotas, templates Jinja2 e arquivos estaticos.
- `data`: arquivos JSON usados como armazenamento inicial.
- `tests`: testes basicos com pytest.

## Motor narrativo

O motor narrativo usa tabelas internas controladas para criar imprevisibilidade
sem integrar IA. Ele pode gerar falas da Ikisaki, consequencias narrativas,
eventos aleatorios, rumores e pressagios da maldicao. Esses resultados nao
estabelecem verdades absolutas nem substituem a decisao do mestre.

Na v0.3.1, eventos, rumores e consequencias aceitam tom opcional:

- `neutro`
- `sombrio`
- `engracado`
- `perigoso`
- `misterioso`

Eventos tambem podem usar o tipo de local como contexto, por exemplo `cidade`,
`floresta`, `estrada`, `lago` ou `penhasco`, sem criar descricoes oficiais para
o mapa. O motor evita repetir exatamente o mesmo resultado logo em seguida
quando a tabela tem mais de uma opcao.

Ao gerar consequencia, evento, rumor ou pressagio pelo terminal, voce pode
registrar no historico ou descartar o resultado.

## Personagens

A partir da v0.3.2, o MAGIK Engine suporta multiplos personagens. Miko Meu
continua sendo criado automaticamente como personagem inicial e exemplo, mas a
estrutura geral aceita novos personagens com:

- `id`
- nome e classe
- vida maxima e vida atual
- armadura
- equipamentos
- habilidades
- observacoes
- status
- tags
- sistemas especiais simples

Use a opcao `17 - Gerenciar personagens` para listar fichas, ver detalhes,
criar personagens, editar vida/armadura, adicionar ou remover equipamentos e
registrar observacoes. Dano fisico, dano magico, cura, testes e registros de
sessao podem ser associados a um personagem escolhido.

Sistemas especiais como Ikisaki e Cajado Sombrio ainda sao especificos do Miko
Meu por enquanto, mas ficam registrados na ficha em `special_systems` e
`abilities` para facilitar futuras expansoes.

## Habilidades

A v0.4 adiciona um sistema geral de habilidades para qualquer personagem. Cada
habilidade pode registrar id, nome, descricao, tipo, forma de uso, efeito,
custo, limite de uso, usos restantes, teste sugerido e observacoes.

Tipos aceitos:

- `ataque`
- `defesa`
- `suporte`
- `cura`
- `magia`
- `controle`
- `utilidade`
- `transformacao`
- `passiva`
- `unica`

Usos aceitos:

- `livre`
- `1 vez por combate`
- `1 vez por sessao`
- `limitado`
- `passivo`

No terminal, entre em `17 - Gerenciar personagens` e depois em
`9 - Gerenciar habilidades` para listar, adicionar, editar, remover, usar ou
restaurar usos de habilidades. Ao usar uma habilidade, o sistema mostra efeito,
custo, teste sugerido e usos restantes, alem de registrar o uso no historico.

Ikisaki e Cajado Sombrio aparecem como habilidades gerais do Miko Meu, mas seus
sistemas completos continuam nas opcoes especiais do menu principal.

## Criaturas e NPCs

A v0.5 separa entidades nao-jogadoras em dois grupos:

- **Criaturas/inimigos**: entidades que podem entrar em combate, receber dano
  fisico, dano magico e cura.
- **NPCs**: entidades sociais e narrativas, com papel, atitude, rumores, status
  e observacoes.

Use `20 - Gerenciar criaturas/inimigos` para criar, listar, ver ficha, editar
vida/armadura, aplicar dano fisico, aplicar dano magico, curar, alterar status,
registrar observacoes e remover criaturas. Criaturas usam as mesmas regras
oficiais de armadura, dano magico e cura do sistema principal.

Use `21 - Gerenciar NPCs` para criar, listar, ver ficha, alterar atitude,
adicionar rumores, alterar status, registrar observacoes e remover NPCs.

Os arquivos `data/creatures.json` e `data/npcs.json` sao criados
automaticamente se nao existirem ou estiverem vazios. Nenhuma criatura oficial
foi inventada nesta etapa.

## Combate por turnos

A v0.6 adiciona um organizador de combate por turnos. Ele nao decide as acoes
do mestre nem substitui a narrativa: apenas controla ordem, rodada,
participantes, dano, cura, status e historico do combate.

O combate basico em `src/core/combat.py` continua sendo a regra mecanica pura:
escolha de dado de dano, dano fisico contra armadura, dano magico ignorando
armadura e cura. O combate por turnos usa essas mesmas regras para organizar
uma cena com varios participantes.

Use `22 - Gerenciar combates` para:

- criar e listar combates;
- adicionar personagens e criaturas;
- rolar iniciativa;
- iniciar combate;
- ver o turno atual;
- avancar turno e rodada;
- aplicar dano fisico ou magico;
- curar participante;
- alterar status;
- usar habilidade geral de personagem;
- registrar uma acao narrativa livre;
- finalizar combate.

A ordem de turnos e baseada na iniciativa. Ao avancar turno, o sistema pula
participantes mortos ou com vida 0. Quando chega ao fim da lista, uma nova
rodada comeca.

Quando dano ou cura acontece dentro de um combate, o estado do participante e
atualizado no combate e, quando ha referencia segura, tambem na ficha original
do personagem ou criatura. A acao tambem e registrada no historico do combate e
no historico geral da sessao.

## Campanhas e sessoes

A v0.7 adiciona organizacao por campanhas e sessoes de campanha. Uma campanha
guarda o panorama da aventura: personagens participantes, NPCs importantes,
locais importantes, eventos importantes e pendencias abertas ou resolvidas.

Uma sessao de campanha guarda o que aconteceu em uma noite ou encontro de jogo:
numero, titulo, resumo, participantes, local principal, eventos, combates,
recompensas, consequencias, pendencias criadas/resolvidas e observacoes.

Use `23 - Gerenciar campanhas e sessoes` para criar campanhas, pausar,
finalizar, adicionar participantes, registrar pendencias e gerenciar as sessoes.
Dentro do submenu de sessoes, voce pode criar sessoes, iniciar/finalizar,
adicionar participantes, adicionar eventos, associar combates existentes,
registrar recompensas, consequencias, pendencias e atualizar o resumo.

O historico geral em `data/sessions.json` continua existindo para registros
cronologicos livres. Campanhas e sessoes organizadas ficam em
`data/campaigns.json` e `data/campaign_sessions.json`. Eventos antigos nao sao
migrados automaticamente, mas continuam compativeis. Novos registros do
historico geral podem ser vinculados opcionalmente a uma campanha e sessao
especifica.

## IA Narradora Auxiliar

A v0.8.2 adiciona suporte a IA local com Ollama, mantendo a OpenAI API como
segunda opção e o fallback local sem IA como garantia. Ela pode ajudar a
narrar eventos, criar falas de NPC, descrever consequencias, resumir sessoes,
melhorar textos e explicar resultados da Roleta Sombria com base nos dados que
o Python ja calculou.

Regra principal:

- Python decide regras, dados, vida, dano, armadura, rolagens, consequencias e
  estado.
- IA apenas narra, sugere e organiza texto.
- O mestre aprova, registra ou descarta.

Ordem de prioridade:

1. Ollama local;
2. OpenAI API, se `OPENAI_API_KEY` existir;
3. fallback local.

Com Ollama local, nao e preciso pagar creditos de API para usar a narradora
auxiliar. Instale o Ollama, baixe o modelo e deixe o servico local rodando:

```powershell
ollama pull llama3.2:3b
ollama run llama3.2:3b
```

Opcionalmente, configure outro modelo:

```powershell
$env:OLLAMA_MODEL="llama3.2:3b"
```

O endpoint padrao usado pelo MAGIK Engine e `http://localhost:11434`.

Para usar OpenAI API como segunda opcao, configure a variavel de ambiente:

```powershell
$env:OPENAI_API_KEY="sua-chave"
```

Opcionalmente:

```powershell
$env:OPENAI_MODEL="gpt-4o-mini"
$env:MAGIK_AI_ENABLED="true"
```

Nao coloque chaves no codigo, nao salve em JSON e nao commite `.env`. O projeto
inclui `.env` e `.env.local` no `.gitignore`.

Se Ollama nao responder e `OPENAI_API_KEY` nao existir, ou se todas as chamadas
falharem, o MAGIK Engine continua funcionando normalmente usando o motor
narrativo local sem IA. Nesse caso, a saida vem marcada como `fallback`.

Use `24 - IA Narradora Auxiliar` no terminal para:

- verificar status da IA;
- narrar evento;
- narrar consequencia;
- narrar resultado da Roleta Sombria;
- gerar fala de NPC;
- resumir sessao;
- executar um teste rapido da IA.

Nenhum texto gerado pela IA e registrado automaticamente. O terminal pergunta
se o mestre quer registrar ou descartar, e permite vincular o registro a uma
campanha/sessao quando fizer sentido.

Para testar sem chave, deixe `OPENAI_API_KEY` ausente e rode:

```powershell
python main.py
```

No menu, entre em `24 - IA Narradora Auxiliar`, use `1 - Verificar status da IA`
e depois `7 - Executar teste rapido da IA`. O terminal mostra status do Ollama
local, modelo configurado, status da OpenAI API, fallback local e a origem da
resposta: `ollama`, `ai` ou `fallback`.

Para configurar depois, defina `OPENAI_API_KEY` apenas no ambiente da sua
maquina antes de rodar o programa. A chave nao e salva pelo MAGIK Engine e nao
deve aparecer no terminal, em JSON ou em commits.

A IA continua sendo apenas narradora auxiliar: ela nao decide dano, vida,
armadura, resultado de dado, morte de personagem, consequencia obrigatoria ou
alteracao de estado. O mestre sempre aprova, registra ou descarta.

## Uso no terminal

As opcoes principais foram pensadas para uso rapido durante a mesa:

- `1`: atalho para ver a ficha do Miko Meu.
- `3` e `4`: sistemas especiais do Miko Meu, Ikisaki e Cajado Sombrio.
- `5` e `6`: registrar e consultar historico da sessao.
- `7`, `8`, `9` e `18`: testes, dano fisico, dano magico e cura com selecao de personagem.
- `12` a `16`: geradores narrativos sem IA.
- `17`: gerenciamento geral de personagens.
- `19`: roteiro recomendado para teste manual.
- `20`: gerenciamento de criaturas, inimigos e chefes.
- `21`: gerenciamento de NPCs sociais e narrativos.
- `22`: organizador de combate por turnos.
- `23`: organizacao de campanhas e sessoes.
- `24`: narracao auxiliar opcional com IA ou fallback local.

Quando uma acao envolve personagem, o terminal lista os personagens disponiveis
com numero, nome, classe e id. Voce pode escolher pelo numero ou pelo id.

## Teste manual recomendado

Use a opcao `19 - Roteiro de teste manual` e passe por este fluxo:

1. Ver ficha de um personagem.
2. Rolar `1d20`.
3. Fazer teste de Vontade.
4. Usar Roleta Sombria da Ikisaki.
5. Gerar consequencia narrativa.
6. Registrar no historico.
7. Aplicar dano fisico.
8. Aplicar dano magico.
9. Curar personagem.
10. Ver historico.

## Estado atual

Esta versao inclui:

- Rolagem de dados no formato `1d20`, `1d10`, `2d6` etc.
- Suporte a multiplos personagens, com Miko Meu como ficha inicial.
- Sistema geral de habilidades por personagem.
- Sistema de criaturas/inimigos e NPCs separado de personagens jogadores.
- Combate por turnos com iniciativa, rodada, turno atual, dano, cura, status e historico.
- Campanhas e sessoes organizadas, com combates associados e pendencias.
- IA Narradora Auxiliar opcional, com fallback local sem IA.
- Interface web inicial com listagem, ficha e criacao de personagens.
- Roleta Sombria: Dez Elos de Ikisaki.
- Cajado Sombrio como alternativa quando Ikisaki estiver indisponivel.
- Registro e consulta de historico de sessao em `data/sessions.json`.
- Sistema oficial de dano com escolha entre `d5`, `d10`, `d20` e `d30`.
- Armadura como camada separada da vida para dano fisico.
- Dano magico ignorando armadura e cura limitada pela vida maxima.
- Testes oficiais `1d20`: Percepcao, Furtividade, Forca, Agilidade,
  Conhecimento, Persuasao e Vontade.
- Moeda Pedralume com conversao, soma, subtracao e exibicao organizada.
- Locais conhecidos do mundo em `data/world_state.json`, sem descricoes
  inventadas.
- Motor narrativo sem IA para falas da Ikisaki, consequencias, eventos,
  rumores e pressagios, com controle de tom e contexto por tipo de local.
