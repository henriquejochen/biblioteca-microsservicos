from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Emprestimo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Só guardamos o id dos outros serviços (sem ForeignKey entre bancos).
    leitor_id = db.Column(db.Integer, nullable=False)
    livro_id = db.Column(db.Integer, nullable=False)
    data_emprestimo = db.Column(db.DateTime, nullable=False, default=datetime.now)
    data_prevista = db.Column(db.DateTime, nullable=False)
    data_devolucao = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="ativo")  # ativo | devolvido

    def para_dict(self):
        return {
            "id": self.id,
            "leitor_id": self.leitor_id,
            "livro_id": self.livro_id,
            "data_emprestimo": self.data_emprestimo.isoformat(timespec="seconds"),
            "data_prevista": self.data_prevista.isoformat(timespec="seconds"),
            "data_devolucao": self.data_devolucao.isoformat(timespec="seconds") if self.data_devolucao else None,
            "status": self.status,
        }
