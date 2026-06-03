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

## Uso no terminal

As opcoes principais foram pensadas para uso rapido durante a mesa:

- `1`: atalho para ver a ficha do Miko Meu.
- `3` e `4`: sistemas especiais do Miko Meu, Ikisaki e Cajado Sombrio.
- `5` e `6`: registrar e consultar historico da sessao.
- `7`, `8`, `9` e `18`: testes, dano fisico, dano magico e cura com selecao de personagem.
- `12` a `16`: geradores narrativos sem IA.
- `17`: gerenciamento geral de personagens.
- `19`: roteiro recomendado para teste manual.

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

Nao ha integracao com IA nesta etapa.
