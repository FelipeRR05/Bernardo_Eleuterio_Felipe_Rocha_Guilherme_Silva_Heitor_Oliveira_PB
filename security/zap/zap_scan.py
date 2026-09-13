"""Scan passivo OWASP ZAP contra a API local.

Uso:  python3 zap_scan.py <porta_da_api> <rotulo> <usuario> <senha>
"""

import http.client
import json
import sys
import time
import urllib.parse
import urllib.request

PORTA_API = sys.argv[1] if len(sys.argv) > 1 else "8000"
ROTULO = sys.argv[2] if len(sys.argv) > 2 else "tp2"
USUARIO = sys.argv[3] if len(sys.argv) > 3 else "ana"
SENHA = sys.argv[4] if len(sys.argv) > 4 else "ana12345"

ALVO = f"http://127.0.0.1:{PORTA_API}"
ZAP_HOST, ZAP_PORTA = "127.0.0.1", 8090
CHAVE = "tp2chave"


def zap_api(caminho: str, **parametros) -> dict:
    """Chama a API de controle do ZAP (conexão direta, sem proxy)."""

    parametros["apikey"] = CHAVE
    url = f"http://{ZAP_HOST}:{ZAP_PORTA}/JSON/{caminho}/?{urllib.parse.urlencode(parametros)}"
    abridor = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with abridor.open(url, timeout=180) as resposta:
        return json.loads(resposta.read())


def via_proxy(metodo: str, caminho: str, corpo=None, cabecalhos=None, json_body=False):
    """Envia uma requisição para a API ATRAVÉS do proxy do ZAP."""

    cabecalhos = dict(cabecalhos or {})
    dados = None

    if corpo is not None:
        if json_body:
            dados = json.dumps(corpo).encode()
            cabecalhos["Content-Type"] = "application/json"
        else:
            dados = urllib.parse.urlencode(corpo).encode()
            cabecalhos["Content-Type"] = "application/x-www-form-urlencoded"

    conexao = http.client.HTTPConnection(ZAP_HOST, ZAP_PORTA, timeout=60)
    try:
        # URI absoluta => o ZAP atua como proxy e registra a transação.
        conexao.request(metodo, f"{ALVO}{caminho}", body=dados, headers=cabecalhos)
        resposta = conexao.getresponse()
        return resposta.status, resposta.read().decode("utf-8", "replace")
    finally:
        conexao.close()


print("=" * 72)
print(f"SCAN PASSIVO OWASP ZAP - alvo {ALVO} (rótulo: {ROTULO})")
print("=" * 72)

# ---------------------------------------------------------------------------
# 1. Autenticação (a própria requisição já é escaneada)
# ---------------------------------------------------------------------------
status, corpo = via_proxy(
    "POST", "/auth/token", corpo={"username": USUARIO, "password": SENHA}
)
print(f"\nPOST /auth/token -> HTTP {status}")

token = json.loads(corpo)["access_token"] if status == 200 else None
auth = {"Authorization": f"Bearer {token}"} if token else {}

# ---------------------------------------------------------------------------
# 2. Percorre a superfície da API gerando tráfego para o scan passivo
# ---------------------------------------------------------------------------
requisicoes = [
    ("GET", "/health", None, {}, False),
    ("GET", "/docs", None, {}, False),          # página HTML (Swagger UI)
    ("GET", "/redoc", None, {}, False),         # página HTML (ReDoc)
    ("GET", "/openapi.json", None, {}, False),
    ("GET", "/", None, {}, False),
    ("GET", "/tickets/", None, auth, False),
    ("GET", "/tickets/1", None, auth, False),
    ("GET", "/tickets/2", None, auth, False),
    ("GET", "/tickets/3", None, auth, False),
    ("GET", "/tickets/", None, {}, False),      # sem token
    ("GET", "/tickets/9999", None, auth, False),
    (
        "POST", "/tickets/",
        {"titulo": f"Chamado do scan {ROTULO}", "descricao": "Tráfego para o ZAP."},
        auth, True,
    ),
    ("POST", "/predict", {"text": "Meu produto parou de funcionar."}, auth, True),
    ("POST", "/predict", {"text": "teste"}, {}, True),  # sem token
    ("GET", "/admin", None, auth, False),        # rota inexistente (404)
    ("GET", "/.env", None, {}, False),           # arquivo sensível (404 esperado)
]

print("\nTráfego enviado através do proxy do ZAP:")
for metodo, caminho, corpo_req, cabecalhos, eh_json in requisicoes:
    try:
        status, _ = via_proxy(metodo, caminho, corpo_req, cabecalhos, eh_json)
        print(f"  {metodo:5s} {caminho:20s} -> HTTP {status}")
    except Exception as erro:  # noqa: BLE001
        print(f"  {metodo:5s} {caminho:20s} -> ERRO: {erro}")

# ---------------------------------------------------------------------------
# 3. Aguarda o scan passivo processar toda a fila
# ---------------------------------------------------------------------------
print("\nAguardando a fila do scan passivo...")
for _ in range(120):
    restantes = int(zap_api("pscan/view/recordsToScan")["recordsToScan"])
    if restantes == 0:
        print("Fila vazia - scan passivo concluído.")
        break
    time.sleep(2)

# ---------------------------------------------------------------------------
# 4. Coleta e exporta os alertas
# ---------------------------------------------------------------------------
alertas = zap_api("alert/view/alerts", baseurl=ALVO, start="0", count="9999")["alerts"]

resumo: dict[tuple[str, str], int] = {}
for alerta in alertas:
    risco = alerta["risk"]
    resumo[(risco, alerta["alert"])] = resumo.get((risco, alerta["alert"]), 0) + 1

ordem = {"High": 0, "Medium": 1, "Low": 2, "Informational": 3}
print("\n" + "=" * 72)
print(f"ALERTAS - {ROTULO}")
print("=" * 72)
for (risco, nome), quantidade in sorted(resumo.items(), key=lambda i: (ordem.get(i[0][0], 9), i[0][1])):
    print(f"[{risco:13s}] {nome}  (x{quantidade})")

contagem_por_risco = {}
for alerta in alertas:
    contagem_por_risco[alerta["risk"]] = contagem_por_risco.get(alerta["risk"], 0) + 1

print(f"\nTotal: {len(alertas)} alertas -> {contagem_por_risco}")

with open(f"zap_alertas_{ROTULO}.json", "w", encoding="utf-8") as arquivo:
    json.dump(alertas, arquivo, ensure_ascii=False, indent=2)
print(f"Alertas salvos em zap_alertas_{ROTULO}.json")
