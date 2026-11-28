from flask import Blueprint, jsonify, request

import regras

rotas = Blueprint("livros", __name__, url_prefix="/api")


def _nao_encontrado():
    return jsonify(erro="Livro não encontrado."), 404


@rotas.post("/livros")
def criar():
    return jsonify(regras.criar(request.get_json(silent=True) or {}).para_dict()), 201


@rotas.get("/livros")
def listar():
    return jsonify([l.para_dict() for l in regras.listar()])


# BUSCA (usada por Empréstimos): dados do livro, inclusive exemplares disponíveis.
@rotas.get("/livros/<int:livro_id>")
def buscar(livro_id):
    livro = regras.buscar(livro_id)
    return jsonify(livro.para_dict()) if livro else _nao_encontrado()


@rotas.put("/livros/<int:livro_id>")
def atualizar(livro_id):
    livro = regras.atualizar(livro_id, request.get_json(silent=True) or {})
    return jsonify(livro.para_dict()) if livro else _nao_encontrado()


@rotas.patch("/livros/<int:livro_id>/inativar")
def inativar(livro_id):
    livro = regras.inativar(livro_id)
    return jsonify(livro.para_dict()) if livro else _nao_encontrado()


# ALTERAÇÃO (disparada pelo serviço de Empréstimos)
@rotas.patch("/livros/<int:livro_id>/emprestar")
def emprestar(livro_id):
    livro = regras.emprestar(livro_id)
    return jsonify(livro.para_dict()) if livro else _nao_encontrado()


@rotas.patch("/livros/<int:livro_id>/devolver")
def devolver(livro_id):
    livro = regras.devolver(livro_id)
    return jsonify(livro.para_dict()) if livro else _nao_encontrado()
