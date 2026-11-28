# Biblioteca em Microsserviços

Sistemas Distribuídos · Projeto: arquitetura em microsserviços (Python, Flask, SQLite) · Centro Universitário SATC

**Equipe:** Henrique Jochen, Thiago Devilla e Gabriel Camargo

## Documento de requisitos

### Propósito do sistema
Controlar o empréstimo de livros de uma biblioteca: cadastrar leitores e livros, registrar empréstimos e devoluções com controle de estoque (exemplares disponíveis) e cobrar multa automaticamente quando a devolução acontece depois do prazo.

### Usuários
- **Bibliotecário(a):** cadastra leitores e livros, registra empréstimos e devoluções e recebe o pagamento das multas.
- **Leitor:** pessoa cadastrada que retira livros emprestados e, se devolver com atraso, fica com multa em aberto.

### Requisitos funcionais
1. O sistema deve permitir cadastrar, listar, consultar, atualizar e inativar leitores.
2. O sistema deve permitir cadastrar, listar, consultar, atualizar e inativar livros, com a quantidade de exemplares.
3. O sistema deve permitir registrar o empréstimo de um livro a um leitor, validando se o leitor existe, está ativo e não tem multa pendente, e se o livro existe, está ativo e tem exemplar disponível.
4. O sistema deve reduzir o número de exemplares disponíveis do livro quando o empréstimo é registrado.
5. O sistema deve permitir consultar um empréstimo exibindo o nome do leitor e o título do livro.
6. O sistema deve permitir registrar a devolução de um livro, devolvendo o exemplar ao estoque.
7. O sistema deve gerar uma multa (R$ 2,00 por dia de atraso, prazo de 7 dias) quando a devolução ocorrer depois da data prevista.
8. O sistema deve somar o valor da multa na dívida do leitor e bloquear novos empréstimos enquanto houver dívida.
9. O sistema deve permitir pagar a multa, abatendo o valor da dívida do leitor.
10. O sistema deve informar erro claro quando um serviço necessário estiver fora do ar ou demorar demais, e desfazer o que foi gravado se a operação não puder ser concluída.

## Descritivo técnico

Cada microsserviço tem sua pasta, sua porta e seu banco SQLite próprio. Nenhum serviço acessa o banco do outro: a comunicação é somente por requisições HTTP, e cada serviço guarda apenas o `id` dos registros dos outros (sem ForeignKey entre bancos).

| Microsserviço | Porta | Banco | Função |
|---|---|---|---|
| `servico_leitores` | 5001 | `leitores.db` | Cadastro de leitores; informa se o leitor está ativo e quanto deve; recebe ajustes de dívida |
| `servico_livros` | 5002 | `livros.db` | Cadastro de livros e controle de exemplares disponíveis (emprestar/devolver) |
| `servico_emprestimos` | 5003 | `emprestimos.db` | Registra empréstimos e devoluções; orquestra as validações com Leitores, Livros e Multas |
| `servico_multas` | 5004 | `multas.db` | Registra e paga multas por atraso; atualiza a dívida do leitor |

Estrutura de cada serviço (igual à atividade guiada): `app.py` (Flask + Flask-SQLAlchemy/SQLite), `models.py`, `regras.py`, `rotas.py`, `erros.py`, `integracao.py` (módulo com `requests`, tempo limite de 5 s e mensagens de erro claras) e `requirements.txt`.

### Integrações entre os serviços

| # | Tipo | Quem chama | Quem responde | Rota usada | O que faz |
|---|---|---|---|---|---|
| 1 | Busca (GET) | Empréstimos | Leitores | `GET /api/leitores/{id}/ativo` | Verifica se o leitor existe, está ativo e se tem dívida |
| 2 | Busca (GET) | Empréstimos | Livros | `GET /api/livros/{id}` | Verifica se o livro existe, está ativo e tem exemplar disponível |
| 3 | Alteração (PATCH) | Empréstimos | Livros | `PATCH /api/livros/{id}/emprestar` | Reduz em 1 os exemplares disponíveis |
| 4 | Alteração (PATCH) | Empréstimos | Livros | `PATCH /api/livros/{id}/devolver` | Devolve 1 exemplar ao estoque |
| 5 | Alteração (POST) | Empréstimos | Multas | `POST /api/multas` | Cria a multa quando há atraso |
| 6 | Busca (GET) | Multas | Leitores | `GET /api/leitores/{id}/ativo` | Confere se o leitor da multa existe |
| 7 | Alteração (PATCH) | Multas | Leitores | `PATCH /api/leitores/{id}/divida` | Soma (multa) ou abate (pagamento) a dívida do leitor |
| 8 | Busca (GET) | Empréstimos | Leitores e Livros | `GET /api/leitores/{id}` e `GET /api/livros/{id}` | Detalhe do empréstimo com nome e título |

As integrações 1, 2 e 3 atendem ao mínimo exigido (duas buscas e uma alteração); as demais ampliam o fluxo.

### Tratamento de falhas
- **Serviço fora do ar ou lento:** `integracao.chamar()` captura `ConnectionError` e `Timeout` e devolve erro 400 com mensagem clara (ex.: "O serviço LIVROS está indisponível. Tente mais tarde."); o programa não quebra.
- **Compensação:** ao registrar um empréstimo, o registro é gravado e depois o estoque é atualizado; se o estoque falhar, o empréstimo é apagado. O mesmo vale para multas (se a dívida do leitor não for atualizada, a multa é apagada) e para devoluções (se Livros ou Multas falhar, o empréstimo volta para "ativo").
- **Degradação:** o detalhe do empréstimo continua respondendo, com um aviso, se Leitores ou Livros estiver fora do ar.
- **Observabilidade:** cada serviço imprime logs padronizados (`[SERVICO] recebi ... -> respondeu ...`, `>>> ligando para ...`, `<<< respondeu ...`).

## Como executar

1. `py -m venv .venv` e `.venv\Scripts\Activate.ps1`
2. `pip install -r requirements.txt`
3. No VS Code: **Executar e Depurar > Iniciar os 4 serviços** (ou dois cliques em `iniciar_servicos.bat`)
4. Importar `thunder-client-colecao.json` no Thunder Client e rodar a pasta **Integrações** na ordem (1 a 13). Cada serviço cria dados de exemplo ao iniciar (3 leitores — sendo o 3º inativo — e 2 livros).

Cada serviço também responde em `GET /api/health`.

## Publicação (Render)

Cada serviço foi publicado como Web Service com `Root Directory` = pasta do serviço, `Build Command` = `pip install -r requirements.txt` e `Start Command` = `gunicorn app:app`. Variáveis de ambiente (endereço público, sem barra no final). `TIMEOUT_SEGUNDOS=60` é necessário porque, no plano gratuito, um serviço hibernado leva cerca de 1 minuto para acordar (o padrão local é 5 s). Como o disco é temporário, cada serviço recria os dados de exemplo ao iniciar; antes de demonstrar, chame `/api/health` de cada serviço para acordá-los:

| Serviço | Variáveis |
|---|---|
| `servico_leitores` | nenhuma |
| `servico_livros` | nenhuma |
| `servico_emprestimos` | `LEITORES_URL`, `LIVROS_URL`, `MULTAS_URL`, `TIMEOUT_SEGUNDOS=60` |
| `servico_multas` | `LEITORES_URL`, `TIMEOUT_SEGUNDOS=60` |

## Repositório no GitHub

https://github.com/henriquejochen/biblioteca-microsservicos
