# Análise dos findings - scan passivo OWASP ZAP

Ferramenta: OWASP ZAP 2.16.1 em modo daemon.
Scan: passivo, com as 57 regras ativas e sensibilidade máxima.
Alvo: API local em 127.0.0.1:8000.
Requisições: 17, incluindo rotas públicas, autenticadas, sem token, acesso indevido e validações.
Relatórios: relatorio_zap.html e relatorio_zap.json. |

## Resultado consolidado

O scan encontrou 28 alertas:

High: 0
Medium: 4
Low: 2
Informational: 22

Os 4 Medium e 2 Low estão apenas em /docs e /redoc. Nenhum endpoint principal da API apresentou alerta Medium ou High.

---

## Uma correção que o próprio scan revelou

Na primeira rodada, os alertas de unsafe-inline apareceram 6 vezes, pois o /openapi.json também estava recebendo a CSP permissiva.

Foi identificado que isso era um erro de configuração. Como /openapi.json retorna apenas JSON, ele não precisa de scripts ou estilos inline.

A configuração foi corrigida removendo essa rota da política permissiva. Após um novo scan, os 2 alertas relacionados ao /openapi.json desapareceram.

---

## Findings de severidade MEDIUM

O ZAP encontrou um alerta Medium nas páginas /docs e /redoc porque a CSP permite script-src 'unsafe-inline', o que reduz a proteção contra XSS.

Foi corrigido o problema no /openapi.json, que passou a usar a CSP estrita da API. Com isso, os alertas Medium caíram de 6 para 4.

As rotas da API continuam protegidas com:

default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'

O risco em /docs e /redoc foi aceito, pois essas páginas precisam de scripts inline para o Swagger/ReDoc funcionar. Para produção, recomenda-se desabilitar essas páginas.

---

### M-02 - CSP: style-src unsafe-inline

O ZAP identificou um alerta Medium nas páginas /docs e /redoc porque a CSP permite CSS inline (style-src 'unsafe-inline').

Isso reduz uma camada de proteção, embora o risco seja menor que permitir scripts inline. A configuração foi mantida nessas páginas porque o Swagger UI depende desse comportamento.

Nas rotas da API e no /openapi.json, a CSP permanece restrita. O risco foi aceito, pois a documentação não exibe dados controlados pelos usuários.

---

## Findings de severidade LOW

Não são exigidos pelo enunciado, mas documentamos porque estão ligados aos Medium acima.

### L-01 - Cross-Domain JavaScript Source File Inclusion

O ZAP identificou que /docs e /redoc carregam JavaScript de uma CDN externa (cdn.jsdelivr.net) sem verificação de integridade.

Isso representa um possível risco de cadeia de suprimentos, caso a CDN ou o pacote seja comprometido.

O risco foi aceito, pois é um comportamento padrão do FastAPI e afeta apenas a documentação. Em produção, desabilitar /docs e /redoc elimina esse ponto.

---

## Findings Informational

Os 22 alertas informativos não representam vulnerabilidades. Eles são principalmente observações sobre o funcionamento da aplicação:

14 HSTS: causado pelo uso de HTTP no ambiente de teste local; em produção, com HTTPS, o HSTS funciona normalmente.
3 Session Management: identificação do uso de JWT.
2 Authentication Request: identificação do endpoint de login.
2 Modern Web Application: identificação de JavaScript nas páginas /docs e /redoc.
1 Charset Mismatch: detalhe da página /redoc, sem impacto na API.

Ou seja, os alertas são esperados no ambiente de testes e não indicam falhas de segurança relevantes.

---

## O que este scan não cobre

O scan passivo não realiza ataques, então não testa vulnerabilidades como SQL Injection, XSS ou path traversal.

Além disso, o ZAP não verifica o controle de ownership/BOLA, pois não sabe quem é dono de cada predição. Esse controle é validado pelos testes automatizados.

Por isso, um relatório do ZAP sem alertas graves não significa que a API esteja totalmente segura.

---

## Como reproduzir

```bash
# 1. Subir o ZAP em modo daemon
./zap.sh -daemon -host 127.0.0.1 -port 8090 -config api.key=SUACHAVE

# 2. Subir a API (em outro terminal, dentro de fastapi/)
uvicorn main:app --reload

# 3. Configurar o navegador ou o cliente HTTP para usar 127.0.0.1:8090 como proxy
#    e percorrer as rotas da API

# 4. Exportar o relatório
curl "http://127.0.0.1:8090/JSON/reports/action/generate/?apikey=SUACHAVE\
&title=Scan&template=traditional-html&reportDir=<pasta>&reportFileName=relatorio_zap.html"
```
