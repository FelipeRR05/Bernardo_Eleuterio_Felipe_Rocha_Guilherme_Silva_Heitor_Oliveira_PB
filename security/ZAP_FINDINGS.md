# Relatório de Findings - OWASP ZAP

**Ferramenta:** OWASP ZAP 2.16.1 (modo daemon)
**Tipo de scan:** Passivo (`pscan`), com todas as 57 regras habilitadas em *alert threshold* **LOW**
(máxima sensibilidade)
**Data:** 13/09/2026
**Alvo:** API `customer-support-intent-api` rodando localmente

## Relatórios exportados

| Arquivo | Conteúdo |
|---|---|
| [`zap/zap_report_ANTES_tp1.html`](zap/zap_report_ANTES_tp1.html) | Scan da API como entregue no TP1 (linha de base) |
| [`zap/zap_report_ANTES_tp1.json`](zap/zap_report_ANTES_tp1.json) | Mesmo scan, formato JSON |
| [`zap/zap_report_DEPOIS_tp2.html`](zap/zap_report_DEPOIS_tp2.html) | Scan da API com os controles do TP2 |
| [`zap/zap_report_DEPOIS_tp2.json`](zap/zap_report_DEPOIS_tp2.json) | Mesmo scan, formato JSON |

---

## Metodologia

A API do TP1 não tinha nenhum controle de segurança HTTP. Escanear apenas a versão final do TP2
produziria um relatório quase vazio - verdadeiro, mas sem demonstrar **o que** os controles
resolveram. Por isso o scan foi executado em duas etapas:

1. **Linha de base** - a API exatamente como entregue no TP1 (recuperada do commit `c14b7ae`),
   rodando na porta 8001.
2. **Verificação** - a API do TP2, com todos os controles aplicados, em modo produção
   (`APP_ENV=production`), na porta 8000.

Em ambos os casos o tráfego foi gerado através do proxy do ZAP, cobrindo 16 requisições: rotas
públicas, rotas autenticadas, tentativas sem token, acesso a recurso de outro usuário, rotas
inexistentes e sondagem de arquivo sensível (`/.env`).

> **Nota técnica.** As primeiras tentativas de scan registraram pouquíssimo tráfego porque a
> variável de ambiente `no_proxy` da máquina inclui `127.0.0.1`, fazendo o cliente HTTP ignorar o
> proxy do ZAP. A solução foi falar com o proxy diretamente via `http.client`, usando a forma
> absoluta da URI na linha de requisição (`GET http://host/path HTTP/1.1`). Sem essa correção, o
> relatório pareceria limpo apenas porque o ZAP não estava vendo as requisições.

---

## Resultado consolidado

| Severidade | ANTES (TP1) | DEPOIS (TP2) | Variação |
|---|---|---|---|
| **High** | 0 | 0 | - |
| **Medium** | **30** | **0** | **−30** |
| **Low** | 17 | 0 | −17 |
| Informational | 21 | 18 | −3 |
| **Total** | **68** | **18** | **−50** |

**Todos os alertas Medium e Low foram eliminados.** Os 18 alertas restantes são exclusivamente
informativos e estão justificados na seção 3.

---

## 1. Findings de severidade MEDIUM (corrigidos)

### M-01 - Content Security Policy (CSP) Header Not Set

| Campo | Valor |
|---|---|
| **Severidade** | Medium |
| **Confiança** | High |
| **CWE** | [CWE-693](https://cwe.mitre.org/data/definitions/693.html) - Protection Mechanism Failure |
| **WASC** | 15 |
| **Ocorrências** | 15 |
| **Status** | ✅ **Corrigido** |

**O que foi detectado.** Nenhuma resposta da API incluía o cabeçalho `Content-Security-Policy`. O
alerta apareceu em todas as rotas, incluindo `/health`, `/docs` e `/auth/token`.

**Por que é um problema.** A CSP é a última linha de defesa contra XSS: ela instrui o navegador
sobre quais origens podem carregar scripts, estilos, imagens e frames. Sem ela, se qualquer conteúdo
controlado pelo atacante for refletido numa resposta interpretada como HTML, o navegador executa o
script sem restrição. Em uma API JSON o risco é menor que em uma aplicação web, mas não é nulo: um
navegador que interprete a resposta como HTML (ver M-02 e o MIME sniffing) reabre o vetor. A CSP
também bloqueia injeção de `<base>` e envio de formulários para domínios externos.

**Como foi corrigido.** Middleware `SecurityHeadersMiddleware` (`security/middleware.py`) aplicando
a política mais restritiva possível nas rotas de API:

```
default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'
```

`default-src 'none'` é viável porque a API devolve exclusivamente JSON - não carrega nenhum recurso
externo. Verificado por `test_content_security_policy_restritiva_nas_rotas_de_api`.

---

### M-02 - Missing Anti-clickjacking Header

| Campo | Valor |
|---|---|
| **Severidade** | Medium |
| **Confiança** | Medium |
| **CWE** | [CWE-1021](https://cwe.mitre.org/data/definitions/1021.html) - Improper Restriction of Rendered UI Layers |
| **WASC** | 15 |
| **Ocorrências** | 15 |
| **Status** | ✅ **Corrigido** |

**O que foi detectado.** Ausência dos cabeçalhos `X-Frame-Options` e da diretiva CSP
`frame-ancestors`.

**Por que é um problema.** Sem eles, um site malicioso pode embutir páginas da aplicação em um
`<iframe>` invisível, sobrepô-lo a uma interface enganosa e induzir o usuário a clicar em ações
reais sem perceber - **clickjacking**. O alvo típico é a página `/docs`: um usuário autenticado
poderia ser levado a disparar requisições autenticadas (criar, alterar ou apagar recursos) achando
que interage com outro site.

**Como foi corrigido.** Dois controles redundantes, por camadas:

- `X-Frame-Options: DENY` - compatível com navegadores antigos
- `frame-ancestors 'none'` na CSP - o mecanismo moderno, que substitui o anterior

Verificado por `test_x_frame_options_deny`.

---

## 2. Findings de severidade LOW (corrigidos)

### L-01 - X-Content-Type-Options Header Missing

| Campo | Valor |
|---|---|
| **Severidade** | Low · **Confiança:** Medium · **CWE-693** · 15 ocorrências |
| **Status** | ✅ **Corrigido** |

**O que foi detectado.** Ausência de `X-Content-Type-Options: nosniff`.

**Por que é um problema.** Sem esse cabeçalho, navegadores podem ignorar o `Content-Type` declarado
e "adivinhar" o tipo real pelo conteúdo (*MIME sniffing*). Uma resposta JSON contendo texto
controlado pelo atacante pode ser reinterpretada como HTML e executada - transformando um endpoint
de dados em vetor de XSS. Este finding se combina com M-01: juntos, formam a cadeia completa do
ataque.

**Como foi corrigido.** `X-Content-Type-Options: nosniff` em todas as respostas
(`security/middleware.py`). Verificado por `test_x_content_type_options_nosniff`.

---

### L-02 - Cross-Domain JavaScript Source File Inclusion

| Campo | Valor |
|---|---|
| **Severidade** | Low · **Confiança:** Medium · **CWE-829** · 2 ocorrências (`/docs`, `/redoc`) |
| **Status** | ✅ **Corrigido** |

**O que foi detectado.** As páginas de documentação carregavam JavaScript de uma CDN externa
(`cdn.jsdelivr.net`).

**Por que é um problema.** Confiar em script de terceiro sem verificação de integridade cria uma
dependência da cadeia de suprimentos: se a CDN for comprometida ou o pacote adulterado, código
arbitrário passa a executar no contexto da aplicação, com acesso a tokens e cookies do usuário
autenticado.

**Como foi corrigido.** A documentação interativa (`/docs`, `/redoc` e `/openapi.json`) é
**desabilitada em produção** (`APP_ENV=production`), eliminando a dependência de CDN. Em
desenvolvimento ela é mantida por produtividade, cenário em que o risco é aceitável. Ver `main.py`.

---

## 3. Findings INFORMATIONAL remanescentes (risco aceito)

Os 18 alertas restantes não exigem correção. Estão documentados por transparência.

### I-01 - Strict-Transport-Security Header on Plain HTTP Response

| Campo | Valor |
|---|---|
| **Severidade** | Informational · **Confiança:** High · **CWE-319** · 15 ocorrências |
| **Status** | ⚠️ **Risco aceito - com justificativa** |

**O que foi detectado.** A API envia `Strict-Transport-Security` em respostas servidas sobre HTTP
puro. O ZAP observa, corretamente, que navegadores **ignoram** HSTS fora de HTTPS.

**Por que foi aceito.** O alerta é consequência direta do **ambiente de teste**, não de um defeito
do código. O scan roda em `http://127.0.0.1:8000` porque não há terminação TLS no ambiente local; em
produção a API fica atrás de um proxy reverso com TLS, onde o mesmo cabeçalho passa a ter efeito
pleno. Remover o cabeçalho para "limpar" o relatório seria contraproducente: o alerta é
Informational justamente porque a presença do cabeçalho não causa dano algum sobre HTTP.

**Condição de fechamento:** re-executar o scan contra o ambiente com TLS terminado. O alerta deixa
de existir sem nenhuma alteração de código.

---

### I-02 - Authentication Request Identified

| Campo | Valor |
|---|---|
| **Severidade** | Informational · **Confiança:** Low · 1 ocorrência (`/auth/token`) |
| **Status** | ℹ️ **Não é vulnerabilidade** |

O ZAP apenas registra ter identificado um endpoint de autenticação, para orientar scans
autenticados posteriores. É uma constatação de funcionamento correto - a API de fato tem um endpoint
de login.

---

### I-03 - Session Management Response Identified

| Campo | Valor |
|---|---|
| **Severidade** | Informational · **Confiança:** High · 2 ocorrências |
| **Status** | ℹ️ **Não é vulnerabilidade** |

O ZAP identificou o mecanismo de sessão (o token JWT na resposta do login). Também é uma
constatação de funcionamento esperado.

---

## 4. Findings que não apareceram - e por quê

Vale registrar o que o scan **não** encontrou, já que a ausência resulta de controles implementados
deliberadamente:

| Alerta típico em APIs | Por que não apareceu |
|---|---|
| *Server Leaks Version Information via Server Header* | Cabeçalho `Server` removido (`run.py` + middleware). Presente 15× no scan ANTES, ausente no DEPOIS |
| *Cross-Domain Misconfiguration* (CORS `*`) | CORS com allowlist explícita; nunca curinga |
| *Information Disclosure - Debug Error Messages* | Tratador global de exceções suprime stack traces |
| *Re-examine Cache-control Directives* | `Cache-Control: no-store, no-cache, must-revalidate` em todas as respostas |
| *Charset Mismatch* | Presente no scan ANTES (`/redoc`); some junto com a documentação em produção |
| *Modern Web Application* | Presente no scan ANTES (`/docs`); some junto com a documentação em produção |

---

## 5. Limitações desta auditoria

1. **Scan passivo apenas.** Conforme o enunciado, foi executado apenas o *passive scan*, que analisa
   as respostas do tráfego gerado, sem enviar payloads de ataque. Ele **não** testa SQL injection,
   XSS refletido, path traversal nem falhas de lógica de negócio - para isso seria necessário o
   *active scan*, previsto para a etapa de pentest.

2. **BOLA não é detectável por scan passivo.** O controle de ownership implementado em
   `routes/tickets.py` - provavelmente o mais importante do TP2 - **não aparece** no relatório do
   ZAP, porque a ferramenta não tem como saber que o ticket 1 pertence à Ana e não ao Bruno. Essa
   verificação depende dos testes automatizados
   (`tests/test_security.py::TestBrokenObjectLevelAuthorization`). É um bom lembrete de que um
   relatório ZAP limpo **não** significa uma API segura.

3. **Cobertura limitada à superfície exercitada.** O scan passivo só analisa o que trafegou. As 16
   requisições cobrem toda a superfície atual da API, mas endpoints futuros precisarão de novo scan.

4. **Ambiente sem TLS**, conforme discutido em I-01.

---

## 6. Como reproduzir

```bash
# 1. Subir o ZAP em modo daemon
./zap.sh -daemon -host 127.0.0.1 -port 8090 -config api.key=SUACHAVE

# 2. Subir a API em modo produção
cd fastapi
APP_ENV=production python run.py

# 3. Gerar o tráfego através do proxy do ZAP e coletar os alertas
python security/zap/zap_scan.py 8000 verificacao ana ana12345

# 4. Exportar o relatório HTML
curl "http://127.0.0.1:8090/JSON/reports/action/generate/?apikey=SUACHAVE\
&title=Scan&template=traditional-html&reportDir=/caminho/saida&reportFileName=zap.html"
```

O script `zap/zap_scan.py` está versionado no repositório.
