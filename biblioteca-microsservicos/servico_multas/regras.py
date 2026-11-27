"""Regras de negócio do serviço de Multas (sem Flask, sem rotas).

  criar() -> BUSCA o leitor em Leitores e ALTERA a dívida dele (com compensação)
  pagar() -> ALTERA a dívida do leitor (abate o valor)
"""
import integracao
from erros import RegraDeNegocioError
from models import Multa, db

VALOR_POR_DIA = 2.00  # R$ por dia de atraso


def _inteiro_positivo(dados, campo):
    valor = dados.get(campo)
    if not isinstance(valor, int) or isinstance(valor, bool) or valor < 1:
        raise RegraDeNegocioError(f"O campo '{campo}' deve ser um inteiro maior que zero.")
    return valor


def criar(dados):
    emprestimo_id = _inteiro_positivo(dados, "emprestimo_id")
    leitor_id = _inteiro_positivo(dados, "leitor_id")
    dias = _inteiro_positivo(dados, "dias_atraso")
    valor = round(dias * VALOR_POR_DIA, 2)

    # BUSCA: o leitor existe?
    print(f"[MULTAS] passo 1: pergunto ao LEITORES se o leitor {leitor_id} existe", flush=True)
    resp = integracao.chamar("LEITORES", "GET", f"/api/leitores/{leitor_id}/ativo")
    if resp.status_code == 404:
        raise RegraDeNegocioError("O leitor não existe.")
    integracao.garantir_sucesso(resp, "LEITORES")

    print("[MULTAS] passo 2: gravo a multa no MEU banco (multas.db)", flush=True)
    multa = Multa(emprestimo_id=emprestimo_id, leitor_id=leitor_id, dias_atraso=dias, valor=valor)
    db.session.add(multa)
    db.session.commit()

    # ALTERAÇÃO: o valor da multa entra na dívida do leitor.
    print("[MULTAS] passo 3: peço ao LEITORES para somar o valor na dívida", flush=True)
    try:
        resp = integracao.chamar("LEITORES", "PATCH", f"/api/leitores/{leitor_id}/divida", json={"valor": valor})
        integracao.garantir_sucesso(resp, "LEITORES")
    except Exception:
        print("[MULTAS] deu errado: apago a multa gravada (compensação)", flush=True)
        db.session.delete(multa)
        db.session.commit()
        raise

    print("[MULTAS] pronto: multa registrada", flush=True)
    return multa


def dados_iniciais():
    """Multas nascem de devoluções em atraso; não há dados de exemplo."""


def listar(leitor_id=None):
    consulta = Multa.query
    if leitor_id is not None:
        consulta = consulta.filter_by(leitor_id=leitor_id)
    return consulta.order_by(Multa.id).all()


def buscar(multa_id):
    return db.session.get(Multa, multa_id)


def pagar(multa_id):
    multa = buscar(multa_id)
    if multa is None:
        return None
    if multa.paga:
        raise RegraDeNegocioError("Esta multa já foi paga.")
    print("[MULTAS] peço ao LEITORES para abater o valor da dívida", flush=True)
    resp = integracao.chamar("LEITORES", "PATCH", f"/api/leitores/{multa.leitor_id}/divida",
                             json={"valor": -multa.valor})
    integracao.garantir_sucesso(resp, "LEITORES")
    multa.paga = True
    db.session.commit()
    return multa
