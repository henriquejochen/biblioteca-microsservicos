"""Regras de negócio do serviço de Empréstimos (sem Flask, sem rotas).

Este é o serviço que mais conversa com os outros:
  criar()    -> BUSCA Leitores, BUSCA Livros, ALTERA Livros (com compensação)
  devolver() -> ALTERA Livros e, se houver atraso, cria uma multa no serviço de Multas
"""
from datetime import datetime, timedelta

import integracao
from erros import RegraDeNegocioError
from models import Emprestimo, db

PRAZO_DIAS = 7


def _inteiro(dados, campo):
    valor = dados.get(campo)
    if not isinstance(valor, int) or isinstance(valor, bool):
        raise RegraDeNegocioError(f"O campo '{campo}' deve ser um número inteiro.")
    return valor


def criar(dados):
    leitor_id = _inteiro(dados, "leitor_id")
    livro_id = _inteiro(dados, "livro_id")

    # INTEGRAÇÃO 1 (busca): o leitor existe, está ativo e não tem multa pendente?
    print(f"[EMPRESTIMOS] passo 1: pergunto ao LEITORES sobre o leitor {leitor_id}", flush=True)
    resp = integracao.chamar("LEITORES", "GET", f"/api/leitores/{leitor_id}/ativo")
    if resp.status_code == 404:
        raise RegraDeNegocioError("O leitor não existe.")
    integracao.garantir_sucesso(resp, "LEITORES")
    leitor = resp.json()
    if not leitor["ativo"]:
        raise RegraDeNegocioError("O leitor está inativo.")
    if leitor["divida"] > 0:
        raise RegraDeNegocioError(f"O leitor possui multas pendentes (R$ {leitor['divida']:.2f}).")

    # INTEGRAÇÃO 2 (busca): o livro existe, está ativo e tem exemplar disponível?
    print(f"[EMPRESTIMOS] passo 2: pergunto ao LIVROS sobre o livro {livro_id}", flush=True)
    resp = integracao.chamar("LIVROS", "GET", f"/api/livros/{livro_id}")
    if resp.status_code == 404:
        raise RegraDeNegocioError("O livro não existe.")
    integracao.garantir_sucesso(resp, "LIVROS")
    livro = resp.json()
    if not livro["ativo"]:
        raise RegraDeNegocioError("O livro está inativo.")
    if livro["exemplares_disponiveis"] < 1:
        raise RegraDeNegocioError("Não há exemplares disponíveis deste livro.")

    print("[EMPRESTIMOS] passo 3: gravo o empréstimo no MEU banco (emprestimos.db)", flush=True)
    agora = datetime.now()
    emprestimo = Emprestimo(leitor_id=leitor_id, livro_id=livro_id, data_emprestimo=agora,
                            data_prevista=agora + timedelta(days=PRAZO_DIAS))
    db.session.add(emprestimo)
    db.session.commit()

    # INTEGRAÇÃO 3 (alteração): peço ao LIVROS para tirar 1 exemplar da prateleira.
    print("[EMPRESTIMOS] passo 4: peço ao LIVROS para reservar o exemplar", flush=True)
    try:
        resp = integracao.chamar("LIVROS", "PATCH", f"/api/livros/{livro_id}/emprestar")
        integracao.garantir_sucesso(resp, "LIVROS")
    except Exception:
        # Cada serviço tem seu banco: não há "desfazer tudo" automático.
        # Se o estoque não foi atualizado, apagamos o empréstimo gravado (compensação).
        print("[EMPRESTIMOS] deu errado: apago o empréstimo gravado (compensação)", flush=True)
        db.session.delete(emprestimo)
        db.session.commit()
        raise

    print("[EMPRESTIMOS] pronto: empréstimo concluído", flush=True)
    return emprestimo


def dados_iniciais():
    """Empréstimos dependem de leitores e livros de outros serviços; não há dados de exemplo."""


def listar(leitor_id=None):
    consulta = Emprestimo.query
    if leitor_id is not None:
        consulta = consulta.filter_by(leitor_id=leitor_id)
    return consulta.order_by(Emprestimo.id).all()


def buscar(emprestimo_id):
    return db.session.get(Emprestimo, emprestimo_id)


def detalhar(emprestimo_id):
    """Empréstimo com nome do leitor e título do livro (duas buscas em outros serviços).

    Se um dos serviços estiver fora do ar, mostramos o empréstimo mesmo assim, com um aviso.
    """
    emprestimo = buscar(emprestimo_id)
    if emprestimo is None:
        return None
    resultado = emprestimo.para_dict()
    for chave, destino, caminho in (
        ("leitor", "LEITORES", f"/api/leitores/{emprestimo.leitor_id}"),
        ("livro", "LIVROS", f"/api/livros/{emprestimo.livro_id}"),
    ):
        try:
            resp = integracao.chamar(destino, "GET", caminho)
            resultado[chave] = resp.json() if resp.ok else {"aviso": f"{destino} respondeu {resp.status_code}"}
        except RegraDeNegocioError as erro:
            resultado[chave] = {"aviso": str(erro)}
    return resultado


def _data_devolucao(dados):
    texto = dados.get("data_devolucao")
    if not texto:
        return datetime.now()
    try:
        return datetime.fromisoformat(texto)
    except (TypeError, ValueError):
        raise RegraDeNegocioError("'data_devolucao' deve estar no formato AAAA-MM-DD.")


def devolver(emprestimo_id, dados):
    """'data_devolucao' é opcional e serve para simular um atraso na demonstração."""
    emprestimo = buscar(emprestimo_id)
    if emprestimo is None:
        return None
    if emprestimo.status != "ativo":
        raise RegraDeNegocioError("Este empréstimo já foi devolvido.")
    data = _data_devolucao(dados)
    atraso = max(0, (data.date() - emprestimo.data_prevista.date()).days)

    print("[EMPRESTIMOS] passo 1: marco o empréstimo como devolvido no MEU banco", flush=True)
    emprestimo.status = "devolvido"
    emprestimo.data_devolucao = data
    db.session.commit()

    def desfazer():
        emprestimo.status = "ativo"
        emprestimo.data_devolucao = None
        db.session.commit()

    print("[EMPRESTIMOS] passo 2: peço ao LIVROS para devolver o exemplar à prateleira", flush=True)
    try:
        resp = integracao.chamar("LIVROS", "PATCH", f"/api/livros/{emprestimo.livro_id}/devolver")
        integracao.garantir_sucesso(resp, "LIVROS")
    except Exception:
        print("[EMPRESTIMOS] deu errado: volto o empréstimo para 'ativo' (compensação)", flush=True)
        desfazer()
        raise

    if atraso > 0:
        print(f"[EMPRESTIMOS] passo 3: {atraso} dia(s) de atraso, peço ao MULTAS para cobrar", flush=True)
        try:
            corpo = {"emprestimo_id": emprestimo.id, "leitor_id": emprestimo.leitor_id, "dias_atraso": atraso}
            resp = integracao.chamar("MULTAS", "POST", "/api/multas", json=corpo)
            integracao.garantir_sucesso(resp, "MULTAS")
        except Exception:
            print("[EMPRESTIMOS] multa falhou: desfaço a devolução (compensação)", flush=True)
            desfazer()
            try:  # tira de novo o exemplar que acabamos de devolver ao estoque
                integracao.chamar("LIVROS", "PATCH", f"/api/livros/{emprestimo.livro_id}/emprestar")
            except RegraDeNegocioError:
                print("[EMPRESTIMOS] não consegui reverter o estoque; conferir manualmente", flush=True)
            raise

    print("[EMPRESTIMOS] pronto: devolução concluída", flush=True)
    return emprestimo
