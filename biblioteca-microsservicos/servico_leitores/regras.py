"""Regras de negócio do serviço de Leitores (sem Flask, sem rotas)."""
from erros import RegraDeNegocioError
from models import Leitor, db


def _validar(dados):
    nome = (dados.get("nome") or "").strip()
    email = (dados.get("email") or "").strip()
    if not nome:
        raise RegraDeNegocioError("O campo 'nome' é obrigatório.")
    if "@" not in email:
        raise RegraDeNegocioError("Informe um 'email' válido.")
    return nome, email


def criar(dados):
    nome, email = _validar(dados)
    leitor = Leitor(nome=nome, email=email)
    db.session.add(leitor)
    db.session.commit()
    return leitor


def dados_iniciais():
    """Cria leitores de exemplo se o banco estiver vazio (no Render o .db é apagado)."""
    if Leitor.query.count() == 0:
        db.session.add(Leitor(nome="Maria Silva", email="maria@exemplo.com"))
        db.session.add(Leitor(nome="João Souza", email="joao@exemplo.com"))
        db.session.commit()


def listar():
    return Leitor.query.order_by(Leitor.id).all()


def buscar(leitor_id):
    return db.session.get(Leitor, leitor_id)


def atualizar(leitor_id, dados):
    leitor = buscar(leitor_id)
    if leitor is None:
        return None
    leitor.nome, leitor.email = _validar(dados)
    db.session.commit()
    return leitor


def inativar(leitor_id):
    leitor = buscar(leitor_id)
    if leitor is None:
        return None
    if not leitor.ativo:
        raise RegraDeNegocioError("O leitor já está inativo.")
    leitor.ativo = False
    db.session.commit()
    return leitor


def ajustar_divida(leitor_id, dados):
    """Chamado pelo serviço de Multas: valor positivo soma dívida, negativo abate."""
    leitor = buscar(leitor_id)
    if leitor is None:
        return None
    try:
        valor = float(dados.get("valor"))
    except (TypeError, ValueError):
        raise RegraDeNegocioError("O 'valor' deve ser um número.")
    if valor == 0:
        raise RegraDeNegocioError("O 'valor' não pode ser zero.")
    nova = round(leitor.divida + valor, 2)
    if nova < 0:
        raise RegraDeNegocioError("A dívida do leitor não pode ficar negativa.")
    leitor.divida = nova
    db.session.commit()
    return leitor
