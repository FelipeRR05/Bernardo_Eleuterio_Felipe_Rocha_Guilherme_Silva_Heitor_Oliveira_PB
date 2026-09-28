# Análise da tríade CIA por componente

Documento que acompanha o DFD (`dfd_api.png`).

Na entrega do TP1 nós discutimos segurança de forma geral, mas não chegamos a aplicar a tríade
componente por componente - e o professor apontou isso na correção. Refizemos a análise aqui
percorrendo cada elemento do diagrama e respondendo, para cada um, as três perguntas:

- **Confidencialidade:** o que nesse componente não pode ser visto por quem não deveria?
- **Integridade:** o que não pode ser alterado sem autorização?
- **Disponibilidade:** o que precisa continuar funcionando, e o que o derrubaria?

Cada componente tem também o que já está implementado e o que continua em aberto, porque
achamos mais honesto registrar as lacunas do que dar a entender que está tudo resolvido.

---

## Visão geral

| #   | Componente                                    | O mais crítico                            |
| --- | --------------------------------------------- | ----------------------------------------- |
| C1  | Cliente / Frontend                            | Confidencialidade (o token fica com ele)  |
| C2  | Middlewares (CORS, cabeçalhos, rate limiting) | Disponibilidade                           |
| C3  | `GET /health`                                 | Disponibilidade                           |
| C4  | `POST /auth/token`                            | Confidencialidade                         |
| C5  | `POST /predict`                               | Integridade                               |
| C6  | `GET /predictions/{id}`                       | **Confidencialidade**                     |
| C7  | `database.db`                                 | Confidencialidade e Integridade           |
| C8  | `JWT_SECRET_KEY`                              | **Confidencialidade** (é a chave de tudo) |

---

## C1 - Cliente / Frontend

_Entidade externa, fora da fronteira de confiança. Não controlamos este componente._

**Confidencialidade.** O que precisa ser protegido aqui é o token JWT, que fica guardado no
lado do cliente depois do login. Quem tiver o token age como o usuário até ele expirar. Também
circulam por aqui as credenciais, no momento do login, e o conteúdo das predições do usuário.

**Integridade.** A requisição pode ser adulterada no caminho, e o próprio cliente pode mandar
qualquer coisa - é por isso que tudo que vem daqui é tratado como dado não confiável.

**Disponibilidade.** Do nosso lado, nada a garantir: se o cliente cair, é problema dele.

| Já implementado                                                                        | Em aberto                                                                              |
| -------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| Token com expiração de 30 minutos, o que limita a janela de uso de um token roubado    | O armazenamento do token no cliente é responsabilidade de quem construir o frontend    |
| CORS com allowlist fecha a porta para outro site chamar a API pelo navegador da vítima | Sem HTTPS local, as credenciais trafegam em texto claro no ambiente de desenvolvimento |

---

## C2 - Middlewares (CORS, cabeçalhos de segurança, rate limiting)

**Confidencialidade.** É a camada que impede um site de terceiro de ler respostas autenticadas da
nossa API. A allowlist de CORS é fechada justamente por isso: com `allow_credentials=True`, um
curinga permitiria que qualquer página lesse dados de um usuário logado.

**Integridade.** Os cabeçalhos protegem a integridade da sessão do usuário no navegador:
`X-Frame-Options: DENY` impede clickjacking, e o `X-Content-Type-Options: nosniff` impede que uma
resposta JSON seja reinterpretada como HTML e executada.

**Disponibilidade.** É aqui que ela é defendida de fato. O rate limiting no login evita que
alguém derrube a API martelando `/auth/token` - e isso importa mais do que parece, porque cada
tentativa de login roda um bcrypt, que é lento de propósito. Sem limite, algumas centenas de
requisições simultâneas consomem todo o processador.

| Já implementado                                                                    | Em aberto                                                                                   |
| ---------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| CORS com lista fechada de origens                                                  | Contador do rate limiting fica em memória; com várias réplicas, o limite efetivo multiplica |
| HSTS, X-Frame-Options, X-Content-Type-Options, CSP, Referrer-Policy, Cache-Control | Contagem por IP não segura uma botnet - faltaria um limite por conta                        |
| Rate limiting de 10/min no `/auth/token` e resposta 429 genérica                   | Sem CAPTCHA progressivo após falhas repetidas                                               |

---

## C3 - `GET /health`

**Confidencialidade.** É uma rota pública, então quase nada. O cuidado que tomamos foi **não
devolver informação demais**: a resposta traz só `status` e `service`. Versão da aplicação, estado
do banco ou nome do ambiente ajudariam quem está fazendo reconhecimento da API.

**Integridade.** Baixa criticidade - a rota não altera nada, só lê um valor fixo.

**Disponibilidade.** É o componente mais crítico da tríade neste caso: o health check é o que
o monitoramento consulta para saber se o serviço está de pé. Se ele cair ou mentir, ninguém
descobre que a API parou.

| Já implementado                                     | Em aberto                                                                                          |
| --------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| Resposta enxuta, sem versão nem detalhe de ambiente | O health check não verifica se o banco está acessível - a API pode responder "ok" com o banco fora |
| Coberta pelo rate limiting global                   | -                                                                                                  |

---

## C4 - `POST /auth/token`

**Confidencialidade.** A senha do usuário passa por aqui, e o token sai por aqui. Além disso, há
um vazamento mais sutil a evitar: a própria existência de um usuário. Se a resposta para
"usuário não existe" fosse diferente da de "senha errada", daria para descobrir quais contas
existem testando uma lista de nomes.

**Integridade.** O token precisa ser inforjável. Se alguém conseguir montar um JWT que a API
aceite, toda a autenticação cai junto.

**Disponibilidade.** É o alvo preferido de força bruta e de negação de serviço por consumo de CPU,
pelo custo do bcrypt.

| Já implementado                                                                                                                    | Em aberto                                                                |
| ---------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| Senhas guardadas só como hash bcrypt, com salt por senha                                                                           | Sem HTTPS local, a senha trafega em claro no ambiente de desenvolvimento |
| Mesma resposta 401 para usuário inexistente e senha errada                                                                         | Sem bloqueio temporário de conta após N falhas                           |
| Verificação bcrypt contra hash falso quando o usuário não existe, para igualar o tempo de resposta e impedir enumeração por timing | Sem registro estruturado de tentativas de login para auditoria           |
| JWT assinado em HS256 com algoritmo fixado na decodificação, o que bloqueia o ataque de `alg: none`                                | Sem refresh token nem revogação: um token roubado vale até expirar       |
| Rate limiting de 10 requisições por minuto                                                                                         |                                                                          |

---

## C5 - `POST /predict`

**Confidencialidade.** O texto que o cliente manda pode conter dado pessoal ou informação sobre a
conta dele. A predição gerada fica gravada e só pode ser lida pelo dono.

**Integridade.** É o ponto mais importante desta rota. Duas coisas precisam ser garantidas:

1. **A entrada não pode trazer campo que não pedimos.** É o que o `extra='forbid'` resolve - sem
   ele, o Pydantic descartaria campos desconhecidos em silêncio, e uma tentativa de enviar
   `owner_id` no corpo passaria despercebida nos logs.
2. **O dono da predição é decidido pelo servidor.** O `owner_id` vem sempre do token, nunca do
   corpo da requisição. O schema de entrada nem declara esse campo.

**Disponibilidade.** Cada chamada faz uma escrita no banco. Num volume alto, o SQLite vira
gargalo, porque serializa as escritas.

| Já implementado                                   | Em aberto                                                            |
| ------------------------------------------------- | -------------------------------------------------------------------- |
| `extra='forbid'`: campo não declarado devolve 422 | Sem limite de quantas predições um usuário pode criar                |
| `owner_id` derivado do token, nunca do corpo      | SQLite não aguenta escrita concorrente em volume                     |
| Tamanho do texto limitado a 5000 caracteres       | O texto é gravado como veio; não há sanitização para exibição futura |
| Rota exige JWT válido                             |                                                                      |

---

## C6 - `GET /predictions/{id}`

**Confidencialidade.** É o componente onde a confidencialidade mais pesa em todo o sistema. É
aqui que mora o risco de BOLA: se a rota devolver a predição sem conferir de quem ela é, qualquer
usuário autenticado lê o conteúdo de qualquer outro só trocando o número na URL.

Há ainda um segundo vazamento, mais discreto: mesmo negando o acesso, responder 403 já
confirmaria que aquele ID existe. Com isso dá para mapear a base inteira por tentativa e erro. Por
isso escolhemos responder 404 tanto para "não existe" quanto para "não é sua" - de fora, as
duas situações ficam idênticas.

**Integridade.** A rota só lê, então o risco é indireto: ela não pode devolver dado de outro
usuário como se fosse do solicitante.

**Disponibilidade.** Consulta simples e indexada por `owner_id`; não é um ponto de pressão.

| Já implementado                                                                  | Em aberto                                                                        |
| -------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| Comparação `owner_id == usuário autenticado` antes de devolver qualquer coisa    | Sem log de tentativas de acesso negado, que seria o sinal de alguém varrendo IDs |
| 404 em vez de 403, para não confirmar a existência do recurso                    | IDs são sequenciais e previsíveis; UUID dificultaria a varredura                 |
| Na listagem, o filtro por dono vai dentro da consulta SQL, não depois em memória |                                                                                  |
| Coberto por teste automatizado (`test_usuario_nao_acessa_predicao_de_outro`)     |                                                                                  |

---

## C7 - `database.db` (SQLite)

**Confidencialidade.** Guarda os hashes de senha e todas as predições dos usuários. É o
componente que concentra mais dado sensível. Nenhuma requisição chega até ele diretamente: todo
acesso passa por um processo dentro da fronteira de confiança.

**Integridade.** É crítica em dois níveis: o dado não pode ser alterado por quem não deveria
(daí o cuidado com SQL injection), e a relação entre predição e dono precisa se manter coerente,
senão o controle de ownership perde o sentido.

**Disponibilidade.** Se o arquivo corromper ou sumir, a aplicação para inteira. É um ponto único
de falha.

| Já implementado                                                                                                      | Em aberto                                                |
| -------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------- |
| Todas as consultas da API passam pelo SQLModel, com valores como parâmetro - não existe SQL montado por concatenação | O arquivo não é criptografado em repouso                 |
| Senhas só em hash bcrypt, nunca em texto                                                                             | Sem rotina de backup                                     |
| `hashed_password` nunca aparece em resposta: as rotas devolvem só os modelos de saída, que não têm esse campo        | SQLite é ponto único de falha e não escala para produção |
| Chave estrangeira `owner_id` referenciando `user.id`                                                                 | Sem auditoria de quem alterou o quê                      |

---

## C8 - `JWT_SECRET_KEY`

**Confidencialidade.** É o segredo mais crítico do sistema inteiro. Quem tiver essa chave
consegue assinar um token válido para qualquer usuário - e aí não adianta nada o resto dos
controles: o atacante entra pela porta da frente, autenticado.

**Integridade.** A chave não pode ser trocada por um valor conhecido pelo atacante. Se isso
acontecer, ele passa a conseguir forjar tokens.

**Disponibilidade.** Se a chave se perder, todos os tokens em circulação viram inválidos de uma
vez e todo mundo precisa logar de novo.

| Já implementado                                                                                            | Em aberto                                                                                                             |
| ---------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| Lida de variável de ambiente, podendo ser trocada sem mexer no código                                      | O valor padrão está no `config.py` para facilitar o desenvolvimento - em produção precisa vir de um cofre de segredos |
| Algoritmo fixado na decodificação (`algorithms=["HS256"]`), o que impede o ataque de confusão de algoritmo | Sem rotação periódica da chave                                                                                        |
| A chave nunca sai em nenhuma resposta da API                                                               |                                                                                                                       |

---

## Onde cada pilar está mais e menos protegido

**Confidencialidade** - é o pilar mais bem coberto. Senha só em hash, `hashed_password` nunca
serializado, ownership verificado nas rotas por ID, 404 em vez de 403 para não confirmar
existência de recurso, CORS fechado e mensagens de erro que não distinguem usuário inexistente de
senha errada. A lacuna principal é o HTTPS: enquanto a API roda em HTTP no ambiente local,
tudo trafega em claro, e o HSTS que enviamos só passa a ter efeito quando houver TLS na frente.

**Integridade** - bem coberta na entrada, fraca na auditoria. A validação do Pydantic com
`extra='forbid'`, o `owner_id` vindo do token e as consultas parametrizadas cobrem bem o que entra
no sistema. O que falta é o outro lado: não temos registro de quem fez o quê. Se algo for
alterado indevidamente, não há trilha para investigar.

**Disponibilidade** - é o pilar mais fraco dos três. O rate limiting no login ajuda, mas o SQLite
é ponto único de falha, não há backup, o health check não verifica o banco e não existe
monitoramento de nada. É o que priorizaríamos se o sistema fosse para produção de verdade.
