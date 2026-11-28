"""Regras de negócio do serviço de Livros (sem Flask, sem rotas)."""
from erros import RegraDeNegocioError
from models import Livro, db


def _texto(dados, campo):
    valor = (dados.get(campo) or "").strip()
    if not valor:
        raise RegraDeNegocioError(f"O campo '{campo}' é obrigatório.")
    return valor


def criar(dados):
    titulo, autor = _texto(dados, "titulo"), _texto(dados, "autor")
    total = dados.get("exemplares", 1)
    if not isinstance(total, int) or isinstance(total, bool) or total < 1:
        raise RegraDeNegocioError("'exemplares' deve ser um inteiro maior ou igual a 1.")
    livro = Livro(titulo=titulo, autor=autor, exemplares_total=total, exemplares_disponiveis=total)
    db.session.add(livro)
    db.session.commit()
    return livro


def dados_iniciais():
    """Cria livros de exemplo se o banco estiver vazio (no Render o .db é apagado)."""
    if Livro.query.count() == 0:
        db.session.add(Livro(titulo="Dom Casmurro", autor="Machado de Assis",
                             exemplares_total=2, exemplares_disponiveis=2))
        db.session.add(Livro(titulo="Memórias Póstumas de Brás Cubas", autor="Machado de Assis",
                             exemplares_total=1, exemplares_disponiveis=1))
        db.session.commit()


def listar():
    return Livro.query.order_by(Livro.id).all()


def buscar(livro_id):
    return db.session.get(Livro, livro_id)


def atualizar(livro_id, dados):
    livro = buscar(livro_id)
    if livro is None:
        return None
    livro.titulo, livro.autor = _texto(dados, "titulo"), _texto(dados, "autor")
    db.session.commit()
    return livro


def inativar(livro_id):
    livro = buscar(livro_id)
    if livro is None:
        return None
    if not livro.ativo:
        raise RegraDeNegocioError("O livro já está inativo.")
    livro.ativo = False
    db.session.commit()
    return livro


def emprestar(livro_id):
    """Chamado pelo serviço de Empréstimos: tira 1 exemplar da prateleira."""
    livro = buscar(livro_id)
    if livro is None:
        return None
    if not livro.ativo:
        raise RegraDeNegocioError("O livro está inativo.")
    if livro.exemplares_disponiveis < 1:
        raise RegraDeNegocioError("Não há exemplares disponíveis.")
    livro.exemplares_disponiveis -= 1
    db.session.commit()
    return livro


def devolver(livro_id):
    """Chamado pelo serviço de Empréstimos: devolve 1 exemplar à prateleira."""
    livro = buscar(livro_id)
    if livro is None:
        return None
    if livro.exemplares_disponiveis >= livro.exemplares_total:
        raise RegraDeNegocioError("Todos os exemplares já estão na prateleira.")
    livro.exemplares_disponiveis += 1
    db.session.commit()
    return livro
