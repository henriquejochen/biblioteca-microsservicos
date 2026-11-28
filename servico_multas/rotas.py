from flask import Blueprint, jsonify, request

import regras

rotas = Blueprint("multas", __name__, url_prefix="/api")


def _nao_encontrado():
    return jsonify(erro="Multa não encontrada."), 404


@rotas.post("/multas")
def criar():
    return jsonify(regras.criar(request.get_json(silent=True) or {}).para_dict()), 201


@rotas.get("/multas")
def listar():
    leitor_id = request.args.get("leitor_id", type=int)
    return jsonify([m.para_dict() for m in regras.listar(leitor_id)])


@rotas.get("/multas/<int:multa_id>")
def buscar(multa_id):
    multa = regras.buscar(multa_id)
    return jsonify(multa.para_dict()) if multa else _nao_encontrado()


@rotas.patch("/multas/<int:multa_id>/pagar")
def pagar(multa_id):
    multa = regras.pagar(multa_id)
    return jsonify(multa.para_dict()) if multa else _nao_encontrado()
