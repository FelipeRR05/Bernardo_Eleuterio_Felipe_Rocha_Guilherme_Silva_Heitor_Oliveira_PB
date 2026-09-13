# Rate Limiting no Endpoint de Autenticação

**Endpoint protegido:** `POST /auth/token`
**Limite configurado:** **5 requisições por minuto, por endereço IP**
**Implementação:** `slowapi` - `security/rate_limit.py` e `routes/auth.py`
**OWASP:** A07:2021 - Identification and Authentication Failures

---

## 1. Por que o endpoint de login precisa de um limite próprio

O `/auth/token` é o único endpoint da API que aceita credenciais e devolve um token válido. Isso o
torna o alvo natural de três ataques:

| Ataque | Como funciona | O que o limite impede |
|---|---|---|
| **Força bruta** | Testar milhares de senhas contra um usuário conhecido | Reduz a taxa de tentativas a um patamar inviável |
| **Password spraying** | Testar uma senha comum (`123456`) contra muitos usuários | Limita a varredura a partir de um mesmo IP |
| **Negação de serviço por CPU** | bcrypt é deliberadamente lento; cada tentativa custa CPU do servidor | Impede que um atacante sature o servidor com logins |

O terceiro ponto costuma passar despercebido: o bcrypt protege as senhas justamente por ser lento
(~100 ms por verificação). Sem rate limiting, essa proteção **vira um vetor de DoS** - poucas
centenas de requisições simultâneas de login consomem todo o CPU disponível. Aqui, o limite protege
tanto as contas quanto a disponibilidade do serviço.

---

## 2. Justificativa técnica do valor escolhido

### O limite: 5 tentativas por minuto, por IP

**Do ponto de vista do usuário legítimo.** Uma pessoa que errou a senha tenta de novo duas, talvez
três vezes, antes de recorrer à recuperação de conta. Cinco tentativas por minuto acomoda esse uso
com folga - inclusive erros de digitação e teclado em layout trocado - sem que alguém legítimo
esbarre no bloqueio.

**Do ponto de vista do atacante.** O limite transforma a aritmética do ataque:

| Cenário | Tentativas/hora | Tempo para varrer 10.000 senhas comuns |
|---|---|---|
| Sem rate limiting | ~36.000 (limitado só pelo bcrypt) | ~17 minutos |
| **Com 5/minuto** | **300** | **~33 horas** |

Uma varredura que levaria menos de 20 minutos passa a exigir mais de um dia inteiro - tempo
suficiente para que o monitoramento detecte o padrão e o IP seja bloqueado. O objetivo do controle
não é tornar o ataque impossível, e sim **caro e ruidoso**.

### Por que não um valor mais baixo (ex.: 3/minuto)

Aumentaria o atrito para o usuário legítimo sem ganho real de segurança: quem consegue 3 tentativas
por minuto também consegue 5, e a ordem de grandeza do ataque permanece a mesma (180 vs. 300
tentativas por hora - ambas inviáveis para uma varredura).

### Por que não um valor mais alto (ex.: 20/minuto)

1.200 tentativas por hora já viabilizam ataques dirigidos contra senhas fracas em poucos dias, o
que enfraquece a proteção sem benefício correspondente para o usuário.

### Alinhamento com referências

O valor está alinhado ao que recomendam o **OWASP Authentication Cheat Sheet** (limitar tentativas
por conta e por origem) e o **NIST SP 800-63B**, seção 5.2.2, que exige mecanismos de limitação de
tentativas em autenticadores baseados em memorização.

---

## 3. Decisões de implementação

### Chave de contagem: endereço IP

O limite é contabilizado por IP de origem (`security/rate_limit.py`). Em produção atrás de um proxy
reverso, o IP real chega no cabeçalho `X-Forwarded-For` - que é **controlado pelo cliente** e só
pode ser considerado confiável se o proxy à frente o sobrescrever.

Por isso esse cabeçalho só é usado quando a aplicação é explicitamente informada de que está atrás
de um proxy confiável, via `TRUST_PROXY_HEADERS=true`. Confiar nele por padrão seria pior que não
ter limite algum: bastaria ao atacante variar o valor do cabeçalho a cada requisição para zerar o
contador.

### Limite global adicional

Além do limite do login, existe um limite padrão de **100 requisições por minuto** para as demais
rotas (`RATE_LIMIT_DEFAULT`), como proteção básica contra varredura automatizada e abuso.

### Resposta ao bloqueio

Quando o limite é excedido, a API responde **HTTP 429 Too Many Requests** com `Retry-After: 60` e
uma mensagem genérica. A mensagem **não informa** quantas tentativas restam nem qual é o limite
configurado - esse dado permitiria ao atacante calibrar a taxa do ataque para ficar logo abaixo do
bloqueio. O teste `test_resposta_429_nao_revela_tentativas_restantes` verifica isso.

---

## 4. Verificação

### Teste automatizado

`tests/test_security.py::TestRateLimiting::test_forca_bruta_no_login_e_bloqueada_com_429` dispara 12
tentativas consecutivas de login com senha errada e exige que o 429 apareça.

Como o rate limiting derrubaria a própria suíte de testes (vários testes fazem login), ele é
desligado na fixture `client` e ligado apenas na fixture dedicada `client_com_rate_limit`.

### Verificação manual

```console
$ for i in $(seq 1 8); do
    curl -s -o /dev/null -w "tentativa $i -> HTTP %{http_code}\n" \
      -X POST http://127.0.0.1:8000/auth/token \
      -d "username=ana&password=errada"
  done
tentativa 1 -> HTTP 401
tentativa 2 -> HTTP 401
tentativa 3 -> HTTP 401
tentativa 4 -> HTTP 429
tentativa 5 -> HTTP 429
tentativa 6 -> HTTP 429
tentativa 7 -> HTTP 429
tentativa 8 -> HTTP 429
```

*(Neste exemplo o bloqueio ocorre na 4ª tentativa porque duas requisições de login já haviam sido
feitas no mesmo minuto durante os testes anteriores.)*

---

## 5. Limitações conhecidas

| Limitação | Impacto | Encaminhamento |
|---|---|---|
| **Contador em memória** | Cada réplica da API tem o próprio contador; com N réplicas o limite efetivo é N × 5 | Backend Redis (suportado pelo `slowapi` via `storage_uri`) |
| **Contagem por IP** | Um atacante com botnet ou pool de IPs residenciais contorna o limite | Complementar com limite **por conta** e bloqueio temporário após N falhas no mesmo usuário |
| **NAT corporativo** | Vários usuários legítimos atrás do mesmo IP compartilham a cota | Chave composta (IP + usuário) ou limite por conta |
| **Sem CAPTCHA progressivo** | Não há escalonamento de atrito após falhas repetidas | Adicionar desafio após 3 falhas consecutivas |
| **Sem alerta** | O bloqueio não notifica ninguém | Emitir evento de segurança ao atingir o limite, para o monitoramento |

O reforço mais relevante é o **limite por conta**, que fecha a lacuna da botnet: por mais IPs que o
atacante tenha, as tentativas contra um mesmo usuário continuam somando no mesmo contador.
