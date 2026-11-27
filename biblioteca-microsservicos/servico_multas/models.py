from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Multa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Só guardamos o id dos outros serviços (sem ForeignKey entre bancos).
    emprestimo_id = db.Column(db.Integer, nullable=False)
    leitor_id = db.Column(db.Integer, nullable=False)
    dias_atraso = db.Column(db.Integer, nullable=False)
    valor = db.Column(db.Float, nullable=False)
    paga = db.Column(db.Boolean, nullable=False, default=False)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def para_dict(self):
        return {
            "id": self.id,
            "emprestimo_id": self.emprestimo_id,
            "leitor_id": self.leitor_id,
            "dias_atraso": self.dias_atraso,
            "valor": round(self.valor, 2),
            "paga": self.paga,
            "criado_em": self.criado_em.isoformat(timespec="seconds"),
        }
