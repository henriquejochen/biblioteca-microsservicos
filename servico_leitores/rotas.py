from flask import Blueprint, jsonify, request

import regras

rotas = Blueprint("leitores", __name__, url_prefix="/api")


def _nao_encontrado():
    return jsonify(erro="Leitor não encontrado."), 404


@rotas.post("/leitores")
def criar():
    return jsonify(regras.criar(request.get_json(silent=True) or {}).para_dict()), 201


@rotas.get("/leitores")
def listar():
    return jsonify([l.para_dict() for l in regras.listar()])


@rotas.get("/leitores/<int:leitor_id>")
def buscar(leitor_id):
    leitor = regras.buscar(leitor_id)
    return jsonify(leitor.para_dict()) if leitor else _nao_encontrado()


@rotas.put("/leitores/<int:leitor_id>")
def atualizar(leitor_id):
    leitor = regras.atualizar(leitor_id, request.get_json(silent=True) or {})
    return jsonify(leitor.para_dict()) if leitor else _nao_encontrado()


@rotas.patch("/leitores/<int:leitor_id>/inativar")
def inativar(leitor_id):
    leitor = regras.inativar(leitor_id)
    return jsonify(leitor.para_dict()) if leitor else _nao_encontrado()


# BUSCA (usada por Empréstimos e Multas): "o leitor existe, está ativo e deve quanto?"
@rotas.get("/leitores/<int:leitor_id>/ativo")
def esta_ativo(leitor_id):
    leitor = regras.buscar(leitor_id)
    if leitor is None:
        return _nao_encontrado()
    return jsonify(id=leitor.id, ativo=leitor.ativo, divida=round(leitor.divida, 2))


# ALTERAÇÃO (disparada pelo serviço de Multas): soma ou abate dívida do leitor.
@rotas.patch("/leitores/<int:leitor_id>/divida")
def ajustar_divida(leitor_id):
    leitor = regras.ajustar_divida(leitor_id, request.get_json(silent=True) or {})
    return jsonify(leitor.para_dict()) if leitor else _nao_encontrado()
