"""O "telefone" deste serviço para falar com os outros serviços.

Os endereços podem ser trocados por variáveis de ambiente (necessário no Render):
    LEITORES_URL, LIVROS_URL, EMPRESTIMOS_URL, MULTAS_URL  (sem barra no final)
"""
import os

import requests

from erros import RegraDeNegocioError

# Use 127.0.0.1 e não "localhost": no Windows, "localhost" pode tentar IPv6 antes.
URLS = {
    "LEITORES": os.environ.get("LEITORES_URL", "http://127.0.0.1:5001"),
    "LIVROS": os.environ.get("LIVROS_URL", "http://127.0.0.1:5002"),
    "EMPRESTIMOS": os.environ.get("EMPRESTIMOS_URL", "http://127.0.0.1:5003"),
    "MULTAS": os.environ.get("MULTAS_URL", "http://127.0.0.1:5004"),
}
# Tempo limite de cada chamada. No Render gratuito, um serviço hibernado leva ~1 min
# para acordar: acorde-os antes (/api/health) ou aumente via TIMEOUT_SEGUNDOS.
TIMEOUT = int(os.environ.get("TIMEOUT_SEGUNDOS", "5"))
EU = "LEITORES"


def chamar(destino, metodo, caminho, **kwargs):
    """Faz a chamada HTTP e mostra no terminal. Se o destino falhar, vira erro 400 claro."""
    print(f"[{EU}]   >>> ligando para {destino}: {metodo} {caminho}", flush=True)
    try:
        resposta = requests.request(metodo, URLS[destino] + caminho, timeout=TIMEOUT, **kwargs)
    except requests.exceptions.ConnectionError:
        print(f"[{EU}]   <<< {destino} não atendeu (fora do ar?)", flush=True)
        raise RegraDeNegocioError(f"O serviço {destino} está indisponível. Tente mais tarde.")
    except requests.exceptions.Timeout:
        print(f"[{EU}]   <<< {destino} demorou demais (timeout)", flush=True)
        raise RegraDeNegocioError(f"O serviço {destino} demorou demais (timeout).")
    print(f"[{EU}]   <<< {destino} respondeu {resposta.status_code}", flush=True)
    return resposta


def garantir_sucesso(resposta, destino):
    """Transforma uma resposta de erro do outro serviço em um erro claro para o usuário."""
    if resposta.ok:
        return
    if resposta.status_code == 400:
        motivo = resposta.json().get("erro", "pedido inválido")
        raise RegraDeNegocioError(f"{destino} recusou: {motivo}")
    raise RegraDeNegocioError(f"O serviço {destino} respondeu com erro {resposta.status_code}.")
