# Relatório de Análise Exploratória de Dados

**Projeto:** Sistema de atendimento ao cliente com IA - Projeto de Bloco, Etapa 2 (TP2)
**Dataset:** Customer Support Ticket Dataset (Kaggle / autor: suraj520)
**Notebook de apoio:** [`EDA_Customer_Support_Tickets.ipynb`](EDA_Customer_Support_Tickets.ipynb)
**Grupo:** Bernardo de Moraes Eleuterio, Felipe Roberto Rocha, Guilherme Valentim Ramalho da Silva, Heitor Cella Oliveira

---

## 1. Problema

### Contexto de negócio

O projeto constrói um sistema de atendimento ao cliente apoiado por inteligência artificial. O
componente central planejado é um **classificador de intenção**: a partir da mensagem escrita pelo
cliente ao abrir um chamado, o sistema deve identificar automaticamente o que ele quer - relatar um
problema técnico, questionar uma cobrança, pedir cancelamento, tirar dúvida sobre um produto ou
solicitar reembolso - para então rotear o atendimento, priorizar a fila e, futuramente, automatizar
respostas.

### Pergunta que a EDA precisa responder

> É possível prever a intenção do cliente (`Ticket Type`) a partir dos dados disponíveis -
> especialmente do texto do chamado (`Ticket Description`)?

Essa pergunta é a premissa de toda a Etapa 3 do projeto. Se a resposta for negativa, treinar o
modelo seria desperdício de esforço, e a EDA precisa dizer isso **antes** da modelagem.

### Hipóteses formuladas no TP1

| # | Hipótese | Status após o TP2 |
|---|---|---|
| H1 | Não há uma intenção dominante única entre os chamados | Confirmada (distribuição 19,3% a 20,7%) |
| H2 | Reembolso e falhas de produto são as intenções mais concretas/recorrentes | Não sustentada (diferença não significativa, p = 0,703) |
| H3 | A urgência percebida pelo usuário independe do tipo de problema | **Sustentada por teste formal (p = 0,216)** |

---

## 2. Dados

### Origem e estrutura

| Característica | Valor |
|---|---|
| Fonte | [Kaggle - Customer Support Ticket Dataset](https://www.kaggle.com/datasets/suraj520/customer-support-ticket-dataset) |
| Registros | 8.469 chamados |
| Colunas | 17 |
| Variável-alvo | `Ticket Type` (5 categorias) |
| Arquivo | `data/customer_support_tickets.csv` |

### Composição das colunas

- **Identificação:** `Ticket ID`
- **Dados do cliente:** `Customer Name`, `Customer Email`, `Customer Age`, `Customer Gender`
- **Dados do produto:** `Product Purchased`, `Date of Purchase`
- **Conteúdo do chamado:** `Ticket Type` (alvo), `Ticket Subject`, `Ticket Description`
- **Operacional:** `Ticket Status`, `Ticket Priority`, `Ticket Channel`, `Resolution`,
  `First Response Time`, `Time to Resolution`, `Customer Satisfaction Rating`

### Qualidade dos dados

**Valores ausentes - estruturais, não aleatórios:**

| Coluna | Ausentes | % | Causa |
|---|---|---|---|
| `Resolution` | 5.700 | 67,3% | Só existe em chamados `Closed` |
| `Time to Resolution` | 5.700 | 67,3% | Só existe em chamados `Closed` |
| `Customer Satisfaction Rating` | 5.700 | 67,3% | Só existe em chamados `Closed` |
| `First Response Time` | 2.819 | 33,3% | Nulo apenas em chamados `Open` |

A ausência reflete o estágio do chamado no fluxo de atendimento - por isso os valores foram
**mantidos como `NaN`**, sem imputação, que introduziria informação inexistente.

**Duplicatas:** nenhuma linha completamente duplicada.

**Problema crítico identificado no TP2:** ao derivar o tempo de resolução
(`Time to Resolution` − `First Response Time`), constatou-se que **1.365 dos 2.769 chamados
fechados (49,3%) apresentam tempo negativo** - isto é, a data de resolução registrada é anterior à
data da primeira resposta. Em um fluxo real de atendimento isso é impossível: um chamado não pode
ser resolvido antes de receber a primeira resposta.

### Variáveis derivadas para a análise

O dataset possui apenas duas colunas numéricas nativas, insuficientes para análise de correlação.
Foram construídas:

| Variável | Cálculo |
|---|---|
| `tempo_resolucao_h` | `Time to Resolution` − `First Response Time`, em horas |
| `dias_desde_compra` | `First Response Time` − `Date of Purchase`, em dias |
| `desc_n_palavras` | Contagem de palavras de `Ticket Description` |
| `desc_n_caracteres` | Contagem de caracteres de `Ticket Description` |
| `prioridade_ord` | Codificação ordinal: Low=1, Medium=2, High=3, Critical=4 |

---

## 3. Análise

### 3.1 Análise univariada (TP1)

Todas as variáveis categóricas apresentam distribuição **próxima da uniforme**:

- `Ticket Type`: 5 categorias entre 19,3% e 20,7% - sem classe dominante nem classe rara
- `Ticket Priority`: 4 categorias entre 24,4% e 25,9%
- `Ticket Channel`: 4 categorias entre ~24% e ~26%
- `Customer Gender`: 34,2% / 34,1% / 31,7%
- `Customer Age`: distribuição uniforme entre 18 e 70 anos (média ≈ 44)
- `Customer Satisfaction Rating`: notas 1 a 5 praticamente equiprováveis (média ≈ 2,99)

### 3.2 Análise de correlação (heatmap)

Correlações de Pearson e Spearman sobre as sete variáveis numéricas.

O heatmap apresenta **um único par com correlação forte**: `desc_n_palavras` × `desc_n_caracteres`
(r = 0,913). Esse par é uma **redundância criada na própria engenharia de variáveis** - contar
palavras e contar caracteres do mesmo texto mede a mesma grandeza. Ele não revela nada sobre o
dataset e, por isso, é tratado separadamente.

Excluído esse par, estas são as correlações mais fortes entre variáveis distintas:

| Par de variáveis | Pearson |
|---|---|
| `Customer Satisfaction Rating` × `dias_desde_compra` | 0,0385 |
| `Customer Satisfaction Rating` × `prioridade_ord` | −0,0214 |
| `Customer Satisfaction Rating` × `tempo_resolucao_h` | 0,0199 |
| `tempo_resolucao_h` × `prioridade_ord` | −0,0170 |
| `Customer Age` × `dias_desde_compra` | 0,0150 |
| Todas as demais | \|r\| < 0,015 |

**A maior correlação informativa de todo o dataset é |r| ≈ 0,04.** Pela referência de Cohen, valores
abaixo de 0,10 são considerados *desprezíveis* - descontado o par redundante, o heatmap é
visualmente todo branco.

### 3.3 Scatter plots

Quatro pares foram inspecionados visualmente: idade × satisfação, tempo de resolução × satisfação,
tamanho do texto × prioridade e dias desde a compra × tempo de resolução. Todos produzem **nuvens
retangulares homogêneas**, sem inclinação, agrupamentos ou regiões vazias - o padrão característico
de variáveis independentes. O gráfico de tempo de resolução × satisfação evidencia visualmente o
problema dos tempos negativos: metade dos pontos fica à esquerda do zero.

### 3.4 Teste de hipótese formal

**Hipótese testada:** H3 do TP1 - a urgência do chamado não está associada ao seu desfecho.

**Formulação estatística:**

- **H₀:** a distribuição da nota de satisfação é igual entre chamados `Critical` e `Low`
- **H₁:** as distribuições são diferentes (bicaudal)
- **α** = 0,05

**Escolha do teste:** o teste de Shapiro-Wilk rejeitou a normalidade nos dois grupos
(W ≈ 0,88; p < 10⁻¹⁸), o que torna o **Mann-Whitney U** (não paramétrico) o teste apropriado. O
teste t de Welch foi executado em paralelo, para verificar a robustez da conclusão.

**Resultados:**

| Métrica | Critical | Low |
|---|---|---|
| n | 726 | 644 |
| Média | 2,959 | 3,053 |
| Mediana | 3,0 | 3,0 |
| Desvio-padrão | 1,417 | 1,394 |

| Teste | Estatística | p-valor | Decisão (α = 0,05) |
|---|---|---|---|
| **Mann-Whitney U** | U = 224.913,5 | **0,2161** | Não rejeita H₀ |
| Teste t de Welch | t = −1,2376 | 0,2161 | Não rejeita H₀ |

Tamanho de efeito (correlação rank-biserial): **r = 0,0379** - desprezível.

**Interpretação em linguagem acessível:** o p-valor de 0,216 responde à pergunta *"se não houvesse
nenhuma diferença real entre chamados críticos e de baixa prioridade, qual a chance de observarmos
por acaso uma diferença tão grande quanto a medida?"*. A resposta é **cerca de 22%** - alta demais
para afirmar que a diferença é real. Na prática: clientes com chamados `Critical` deram nota média
2,96 e os de prioridade `Low`, 3,05 - menos de **0,1 ponto** de diferença numa escala de 1 a 5.
A Hipótese 3 do TP1 é **sustentada** pelos dados.

Vale a ressalva metodológica: não rejeitar H₀ não **prova** que os grupos são idênticos; significa
que não encontramos evidência de diferença. Somado às correlações nulas, porém, a explicação mais
provável não é "a prioridade não importa no mundo real", e sim que **este dataset foi gerado
artificialmente**.

### 3.5 Verificação de sinal preditivo para o classificador

Como os metadados não carregam informação, restava verificar a premissa central do projeto: o
**texto** prevê a intenção?

**Teste qui-quadrado de independência - `Ticket Subject` × `Ticket Type`:**

| Métrica | Valor |
|---|---|
| Qui-quadrado | 39,57 (60 g.l.) |
| p-valor | **0,9807** |
| V de Cramér | **0,0342** |

O assunto declarado do chamado é **estatisticamente independente** do tipo do chamado. Num dataset
coerente, um chamado com assunto "Cancellation request" seria quase sempre do tipo
"Cancellation request"; aqui ele se distribui igualmente entre os cinco tipos.

**Baseline de classificação (validação cruzada estratificada, 5 partições):**

| Modelo | Acurácia |
|---|---|
| Acaso puro (1/5 classes) | 20,00% |
| Modelo trivial (sempre a classe majoritária) | 20,69% |
| **TF-IDF + Regressão Logística sobre o texto** | **18,87%** (± 0,84 p.p.) |

O modelo treinado no texto tem desempenho **inferior ao chute da classe mais frequente**.

**Causa raiz:** **5.868 dos 8.469 chamados (69,3%)** começam com exatamente o mesmo texto -
`"I'm having an issue with the {product_purchased}. Please assist."` - e esses chamados se
distribuem igualmente entre as cinco intenções (1.231 / 1.217 / 1.175 / 1.124 / 1.121). O
placeholder `{product_purchased}` sequer foi substituído pelo nome real do produto. Nenhum modelo
consegue separar classes a partir de textos idênticos.

---

## 4. Insights principais

1. **O dataset é sintético, com colunas geradas independentemente entre si.** A evidência é
   convergente e quantitativa: correlação máxima de 0,04 entre variáveis distintas,
   distribuições uniformes em todas as categóricas, independência qui-quadrado entre assunto e tipo
   (p = 0,98) e 49,3% dos chamados com tempo de resolução logicamente impossível.

2. **A prioridade do chamado é um rótulo sem consequência observável.** Testado formalmente:
   chamados `Critical` e `Low` produzem a mesma distribuição de satisfação (p = 0,216, efeito
   r = 0,04). Isso sustenta a Hipótese 3 do TP1.

3. **O texto do chamado não permite prever a intenção.** Um baseline TF-IDF + Regressão Logística
   fica em 18,9% de acurácia, abaixo do modelo trivial (20,7%). A causa é a geração por templates:
   69,3% dos chamados compartilham o mesmo texto de abertura, rotulado com as cinco intenções.

4. **Os valores ausentes são informativos, não ruído.** `Resolution`, `Time to Resolution` e
   `Customer Satisfaction Rating` existem exclusivamente em chamados `Closed`. Qualquer imputação
   destruiria essa semântica - e, num modelo preditivo, usar essas colunas causaria *data leakage*,
   já que elas só existem após o desfecho que se quer prever.

5. **Descobrir a inadequação do dataset é, em si, o resultado mais valioso desta EDA.** A
   constatação foi feita com um baseline de poucas linhas, antes de qualquer investimento em
   modelagem, arquitetura de features ou ajuste de hiperparâmetros.

---

## 5. Limitações

### Do dataset

- **Natureza sintética**: nenhuma conclusão obtida aqui pode ser generalizada para o comportamento
  real de clientes de suporte. As análises descrevem o processo de geração dos dados, não o domínio.
- **Timestamps inconsistentes**: `tempo_resolucao_h` é inutilizável como métrica operacional
  (49,3% de valores negativos).
- **Texto por template**: `Ticket Description` tem diversidade lexical artificialmente baixa e
  contém placeholders não substituídos (`{product_purchased}`).
- **Rótulos aparentemente aleatórios**: não há associação entre `Ticket Type` e nenhuma outra
  coluna, inclusive o assunto e o texto do próprio chamado.

### Da análise

- **O teste de hipótese cobre apenas chamados fechados** (2.769 de 8.469), pois a nota de
  satisfação só existe nesse subconjunto. A conclusão vale para essa fatia.
- **Não rejeitar H₀ não equivale a provar igualdade.** Com n ≈ 700 por grupo, o teste tem poder
  para detectar efeitos moderados, mas efeitos muito pequenos poderiam passar despercebidos - o que
  não altera a conclusão prática, dado o tamanho de efeito medido (r = 0,04).
- **O baseline de classificação é intencionalmente simples.** TF-IDF + Regressão Logística não
  esgota o espaço de modelos; um transformer poderia capturar padrões sutis. Contudo, quando 69,3%
  dos exemplos têm texto idêntico e rótulos distribuídos uniformemente, o limite não é o modelo - é
  a **informação ausente nos dados**.
- **Colunas textuais livres não foram exploradas em profundidade** (`Resolution`,
  `Product Purchased`), por não serem candidatas a preditoras da intenção no desenho atual.

---

## 6. Próximos passos

### Decisão necessária antes da Etapa 3

A Etapa 3 prevê treinar o classificador de intenção. A EDA mostrou que, **com o dataset e a
variável-alvo atuais, esse modelo terá desempenho de acaso**. Há três caminhos viáveis:

| Alternativa | Descrição | Prós | Contras |
|---|---|---|---|
| **A. Trocar o dataset** | Adotar uma base real de intenções, como *Bitext Customer Support*, *CLINC150* ou *Banking77* | Sinal real; métricas com significado; comparável à literatura | Exige refazer a EDA e ajustar o escopo do domínio |
| **B. Trocar a variável-alvo** | Manter o dataset e prever algo que tenha sinal (ex.: `Ticket Status` a partir dos metadados) | Reaproveita todo o trabalho já feito | A EDA indica correlações nulas também entre metadados - sinal improvável |
| **C. Manter como scaffold** | Usar o dataset apenas para exercitar o pipeline (API, segurança, serialização), assumindo o modelo como simulado | Preserva o foco do Projeto de Bloco, que é segurança de aplicações de IA | Não entrega um classificador funcional |

**Recomendação do grupo: alternativa A.** O esforço de substituir o dataset é baixo (a estrutura da
EDA e o pipeline da API são reaproveitáveis integralmente) e é a única opção que entrega um
classificador com desempenho real, tornando o pentest da Etapa 4 mais interessante - uma API que
serve um modelo de verdade tem superfície de ataque maior do que uma que devolve resposta fixa.

### Plano de execução sugerido

1. **Selecionar e validar o novo dataset** aplicando, logo de início, os mesmos testes de sanidade
   criados aqui: correlação entre variáveis, qui-quadrado entre assunto e alvo e baseline
   TF-IDF vs. modelo trivial. Só prosseguir se o baseline superar claramente o trivial.
2. **Estabelecer o baseline oficial** com TF-IDF + Regressão Logística e registrar a métrica.
3. **Evoluir o modelo** (embeddings ou transformer leve tipo DistilBERT), comparando sempre contra
   o baseline.
4. **Avaliar com métricas adequadas**: F1-macro e matriz de confusão, não apenas acurácia.
5. **Integrar o modelo à rota `/predict`**, que já existe e está protegida por JWT, validação
   estrita de entrada (`extra="forbid"`) e rate limiting - a substituição é localizada, sem alterar
   a arquitetura de segurança construída no TP2.
6. **Considerar as ameaças específicas de modelos de IA** na Etapa 4: *prompt injection* no texto de
   entrada, extração de modelo por consultas em massa e negação de serviço por inferência custosa.

---

## 7. Referências

- Dataset: <https://www.kaggle.com/datasets/suraj520/customer-support-ticket-dataset>
- Notebook completo com código e gráficos: [`EDA_Customer_Support_Tickets.ipynb`](EDA_Customer_Support_Tickets.ipynb)
- Cohen, J. (1988). *Statistical Power Analysis for the Behavioral Sciences* - referência para
  interpretação de tamanhos de efeito.
