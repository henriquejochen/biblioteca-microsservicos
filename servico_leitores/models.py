from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Leitor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    divida = db.Column(db.Float, nullable=False, default=0.0)  # multas em aberto (R$)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def para_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "email": self.email,
            "ativo": self.ativo,
            "divida": round(self.divida, 2),
            "criado_em": self.criado_em.isoformat(timespec="seconds"),
        }
