# AGENTS.md

Orientacoes para agentes trabalhando no MAGIK Engine:

- Manter o projeto em Python 3.11+.
- Nao concentrar regras de jogo em `main.py`.
- Separar dominio, sistemas, armazenamento e UI.
- Usar JSON como armazenamento inicial.
- Nao adicionar integracao com IA nesta etapa.
- Preferir funcoes pequenas, tipagem simples e testes com pytest.
- Preservar o papel do mestre: o sistema auxilia, mas nao decide a narrativa sozinho.
