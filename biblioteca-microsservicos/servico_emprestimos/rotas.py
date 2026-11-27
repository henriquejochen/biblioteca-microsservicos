from flask import Blueprint, jsonify, request

import regras

rotas = Blueprint("emprestimos", __name__, url_prefix="/api")


def _nao_encontrado():
    return jsonify(erro="Empréstimo não encontrado."), 404


@rotas.post("/emprestimos")
def criar():
    return jsonify(regras.criar(request.get_json(silent=True) or {}).para_dict()), 201


@rotas.get("/emprestimos")
def listar():
    leitor_id = request.args.get("leitor_id", type=int)
    return jsonify([e.para_dict() for e in regras.listar(leitor_id)])


@rotas.get("/emprestimos/<int:emprestimo_id>")
def buscar(emprestimo_id):
    emprestimo = regras.buscar(emprestimo_id)
    return jsonify(emprestimo.para_dict()) if emprestimo else _nao_encontrado()


# Empréstimo + nome do leitor + título do livro (busca em dois outros serviços).
@rotas.get("/emprestimos/<int:emprestimo_id>/detalhe")
def detalhar(emprestimo_id):
    detalhe = regras.detalhar(emprestimo_id)
    return jsonify(detalhe) if detalhe else _nao_encontrado()


@rotas.patch("/emprestimos/<int:emprestimo_id>/devolver")
def devolver(emprestimo_id):
    emprestimo = regras.devolver(emprestimo_id, request.get_json(silent=True) or {})
    return jsonify(emprestimo.para_dict()) if emprestimo else _nao_encontrado()
