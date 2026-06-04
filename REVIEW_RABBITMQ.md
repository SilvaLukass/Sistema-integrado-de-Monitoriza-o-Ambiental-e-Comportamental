# Revisão da integração RabbitMQ (pub/sub) — guia para retomar

> Documento de apoio para quando voltares dentro de uns dias. Resume **o que foi
> implementado**, **o que deves rever**, **o que deves testar** e as **decisões em
> aberto**. Objetivo: confirmar que a implementação está no melhor estado possível
> antes de avançar para o Raspberry Pi.
>
> Plano de origem: `.cursor/plans/rabbitmq_pub_sub_sensores_518e4058.plan.md`
> Decisões registadas: `DECISOES_LOCAIS.md` (secções 18 e 19)

---

## 1) O que foi implementado (resumo)

A ideia central: meter o **RabbitMQ** como camada de transporte publish/subscribe
entre os sensores e o backend. O simulador deixou de chamar o modelo/BD
diretamente e passou a ser **publisher**; o backend ganhou um **consumer** que
recebe do broker e reutiliza o pipeline que já existia
(`db.add_sensor_reading` + `process_model_readings`). Resultado: publisher e
subscriber ficam desacoplados — hoje o publisher é o simulador, amanhã é o RPi,
sem mexer no backend nem no frontend.

### Ficheiros novos

| Ficheiro | Para que serve |
|----------|----------------|
| `docker-compose.yml` (raiz) | Sobe o broker `rabbitmq:3.13-management` (portas `5672` AMQP, `15672` UI), volume durable e healthcheck. |
| `backend/app/services/messaging.py` | Camada AMQP: `get_connection` (`connect_robust`), `publish_reading` (topic exchange, JSON persistente) e `start_consumer` (queue durable, bind `sensors.#`, prefetch 10, ack manual, reutiliza o pipeline). |
| `REVIEW_RABBITMQ.md` (este ficheiro) | Guia de revisão/teste. |

### Ficheiros alterados

| Ficheiro | Alteração |
|----------|-----------|
| `requirements.txt` | Adicionado `aio-pika`. |
| `backend/app/config.py` | Settings novas: `rabbitmq_url`, `rabbitmq_exchange`, `rabbitmq_queue`, `rabbitmq_routing_key`, `consumer_enabled`. |
| `backend/app/main.py` | No lifespan: abre a ligação AMQP, arranca a `consumer_task`, e cancela/fecha tudo no shutdown. Falha do broker no arranque degrada com aviso (não crasha). Guarda `app.state.settings`. |
| `backend/app/services/simulator.py` | `simulator_loop` passou a **publisher**: publica no broker (`source="simulator"`) em vez de tocar no modelo/BD. Resiliente a broker em baixo. |
| `backend/app/services/db.py` | `H001` ("Humidade - Sala") acrescentado ao `DEVICE_SEED`. |
| `DECISOES_LOCAIS.md` | Secções 18 (decisão RabbitMQ + contrato de mensagem) e 19 (handoff RPi). |

### Arquitetura resultante

```
Simulador (publisher)  --publish JSON-->  Exchange topic "eldercare.sensors"
                                                  |  bind "sensors.#"
                                                  v
                                          Queue "sensor_readings" (durable)
                                                  |  consume + ack manual
                                                  v
                                    Consumer backend (aio-pika)
                                       |-> db.add_sensor_reading
                                       |-> process_model_readings -> alertas/Telegram
                                                  v
                                              SQLite -> Dashboard React
```

---

## 2) Validação local já feita (para confirmares de novo)

Quando implementei, validei isto (corre os testes da secção 4 para reconfirmar):

- Broker arrancou; queue `sensor_readings` ligada ao exchange `eldercare.sensors`
  com routing key `sensors.#`.
- **Taxa de publish == taxa de deliver**, backlog a zero, 1 consumer → o consumer
  acompanha o ritmo.
- `GET /api/sensors/latest` e `GET /api/model/latest` devolvem dados → prova o
  ciclo **publish → consume → modelo → BD**.
- `H001` aparece em `GET /api/devices`.
- **Resiliência:** parei o broker → backend manteve-se vivo (avisos, sem crash);
  reiniciei → `connect_robust` reconectou sozinho e o fluxo retomou.

---

## 3) O que rever (revisão de código)

Lê cada ponto e decide se concordas com a decisão tomada. Marca o que quiseres mudar.

- [ ] **`messaging.py` — uso do `topic` exchange (vs `fanout`).** Justificação:
  mesmo comportamento pub/sub e permite routing futuro por sensor (`sensors.rpi.door`)
  sem reescrever a camada. Confirma se preferes esta defesa ou o `fanout` clássico
  do tutorial.
- [ ] **Ack manual + `message.process()`.** Em caso de exceção a mensagem volta à
  queue (requeue). Revê: faz sentido para ti que uma leitura "má" seja
  re-tentada? Hoje, JSON inválido é descartado (não faz requeue infinito), mas
  uma falha na inferência apenas regista aviso (não rebenta o ack). Confirma se
  este comportamento é o desejado.
- [ ] **`prefetch_count = 10`.** Valor pequeno propositado. Para o ritmo atual
  (1 msg a cada poucos segundos) é mais que suficiente. Revê se queres documentar
  porquê.
- [ ] **Import tardio de `process_model_readings` dentro de `start_consumer`.**
  Foi para evitar import circular (segue o padrão que o simulador já usava). Vê
  se preferes outra organização de módulos.
- [ ] **Simulador resiliente.** Em vez de morrer quando o broker está em baixo,
  faz log de aviso e tenta na iteração seguinte (reabre canal). Confirma que não
  queres backoff/limite de tentativas.
- [ ] **Tratamento de falha do broker no arranque (`main.py`).** Se o broker não
  estiver disponível no boot, o backend arranca na mesma (com aviso) e o
  `connect_robust` liga quando o broker aparecer — **mas** repara que se
  `get_connection` falhar logo, `app.state.rabbitmq` fica `None` e o consumer não
  arranca nessa sessão. Pondera se queres uma retry de arranque do consumer.
- [ ] **`except (asyncio.CancelledError, Exception)` no shutdown.** É
  propositadamente largo para o shutdown nunca rebentar. Vê se preferes algo mais
  específico.
- [ ] **Contrato de mensagem.** `{"source": ..., "readings": {...}}`. Confirma que
  bate certo com o que o RPi vai enviar (secção 19 do `DECISOES_LOCAIS.md`).
- [ ] **`H001` no `DEVICE_SEED`** com `type: "humidity"`. Confirma se o frontend
  trata este `type` (ícone/label) ou se precisa de tradução em `src/locales`.
- [ ] **Credenciais `guest/guest`.** Só funcionam em `localhost`. Para o RPi pela
  rede é preciso utilizador dedicado — está documentado mas ainda **não** feito.

---

## 4) O que testar (checklist reproduzível)

> Pré-requisitos: Docker a correr; venv com dependências do `requirements.txt`
> (inclui `aio-pika`, `fastapi`, `uvicorn[standard]`, `pydantic-settings`, etc.).

### 4.1 Arranque limpo

```bash
# 1. Subir o broker
docker compose up -d rabbitmq

# 2. Confirmar que está saudável
docker inspect --format='{{.State.Health.Status}}' eldercare-rabbitmq   # -> healthy

# 3. Arrancar o backend (a partir da raiz do repo)
PYTHONPATH=. python -m uvicorn backend.app.main:app --reload --port 8000
```

- [ ] Nos logs do backend aparece `Consumer RabbitMQ ligado: exchange=... queue=... binding='sensors.#'`.
- [ ] UI de gestão acessível em `http://localhost:15672` (guest/guest).

### 4.2 Ciclo publish → consume → modelo → BD

```bash
curl -s http://127.0.0.1:8000/health                 # {"ok":true}
curl -s http://127.0.0.1:8000/api/sensors/latest     # devolve readings recentes
curl -s http://127.0.0.1:8000/api/model/latest       # devolve inferência
curl -s http://127.0.0.1:8000/api/devices            # H001 presente
```

- [ ] `/api/sensors/latest` muda de timestamp ao longo do tempo (simulador a publicar).
- [ ] `/api/model/latest` devolve `expected_activity` + `confidence`.
- [ ] `H001` aparece em `/api/devices`.

### 4.3 Saúde da queue (não cresce indefinidamente)

```bash
curl -s -u guest:guest "http://127.0.0.1:15672/api/queues/%2F/sensor_readings" \
  | python -c "import sys,json;d=json.load(sys.stdin);print('ready:',d['messages_ready'],'consumers:',d['consumers'])"
```

- [ ] `messages_ready` mantém-se perto de 0 (consumer acompanha).
- [ ] `consumers` >= 1.

### 4.4 Resiliência (o teste mais importante para a viva)

```bash
docker stop eldercare-rabbitmq
# esperar ~6s
curl -s http://127.0.0.1:8000/health      # ainda {"ok":true} -> backend não crashou
docker start eldercare-rabbitmq
# esperar ~20-30s (boot + reconnect)
curl -s http://127.0.0.1:8000/api/sensors/latest   # timestamp fresco -> fluxo retomou
```

- [ ] Backend sobrevive ao broker em baixo (apenas avisos no log).
- [ ] Após reinício, `connect_robust` reconecta e o fluxo retoma sozinho.

### 4.5 Persistência (durabilidade)

- [ ] Reiniciar o backend e confirmar que leituras antigas continuam em
  `backend/data/eldercare.sqlite` (`/api/sensors/latest` devolve algo).
- [ ] (Opcional) `docker compose down` **sem** `-v` e voltar a subir: o volume
  `rabbitmq_data` mantém-se. Com `-v` apaga.

### 4.6 (Opcional) Simular o RPi sem hardware

Publicar uma mensagem `source: "rpi"` direto no broker e ver se o backend a
consome na mesma (graças ao bind `sensors.#`):

```bash
python - <<'PY'
import asyncio, json, aio_pika
async def main():
    conn = await aio_pika.connect_robust("amqp://guest:guest@localhost:5672/")
    ch = await conn.channel()
    ex = await ch.declare_exchange("eldercare.sensors", aio_pika.ExchangeType.TOPIC, durable=True)
    body = json.dumps({"source":"rpi","readings":{"hour":14,"day_of_week":3,"minute":5,"D001":1,"T001":22.4,"H001":48.0}}).encode()
    await ex.publish(aio_pika.Message(body, delivery_mode=aio_pika.DeliveryMode.PERSISTENT), routing_key="sensors.rpi")
    await conn.close()
asyncio.run(main())
PY
curl -s http://127.0.0.1:8000/api/sensors/latest   # deve refletir a leitura "rpi"
```

- [ ] A leitura com `source: "rpi"` é consumida e persiste (prova que o contrato
  e o routing key do RPi vão funcionar).

---

## 5) Pontos em aberto / possíveis melhorias

Decide quais valem a pena antes de avançar:

- [ ] **Credenciais para rede.** Criar utilizador dedicado (ex.: `eldercare`) +
  password (e talvez vhost) em vez de `guest/guest`, para o RPi alcançar o broker
  pela LAN. Atualizar `rabbitmq_url`.
- [ ] **Variáveis de ambiente / `.env`.** Hoje os defaults estão no `config.py`.
  Considera pôr `RABBITMQ_URL`, `CONSUMER_ENABLED`, etc. no `.env` e documentar.
- [ ] **`requirements.txt` único vs dois.** Existe `requirements.txt` (raiz, deps
  do backend) e `App/requirements.txt` (deps de ML). Confirma se queres unificar
  ou documentar claramente qual usar para o backend. (Eu instalei `aio-pika` +
  deps do backend no `venv` para validar.)
- [ ] **Endpoint `/api/debug/publish` (opcional, passo 7 do plano).** Não foi
  criado — publicar no broker para testar o consumer sem o simulador. O snippet
  da secção 4.6 cobre isto manualmente; pondera formalizá-lo.
- [ ] **Observabilidade.** Logs estruturados por mensagem consumida (source,
  confidence, alert_created) ajudariam na defesa e no debug.
- [ ] **Testes automatizados.** Um teste de contrato (publica → consome → estado)
  com um broker efémero seria bom para regressão.
- [ ] **Dead-letter queue.** Hoje JSON inválido é descartado. Se quiseres
  rastrear mensagens "más", configura uma DLQ.

---

## 6) Próximo passo: Raspberry Pi (não começar antes de fechar o de cima)

Está tudo documentado em `DECISOES_LOCAIS.md` secção 19. Resumo do que falta
**fora deste repo** (trabalho do colega + decisões conjuntas):

1. Decidir onde corre o broker (PC sempre ligado na LAN vs no próprio RPi) e fixar IP/host.
2. Criar credenciais remotas no broker e abrir a porta `5672`.
3. `rpi_agent/` com `pika` (publisher síncrono) a enviar `{source:"rpi", readings:{...}}`
   com routing key `sensors.rpi`, primeiro em `--mock`.
4. Validar end-to-end e, quando o RPi for a fonte principal, desligar o simulador
   (`SIMULATOR_ENABLED=false`) ou mantê-lo só para CO2 sintético.

**Importante:** o backend não muda a partir daqui. Se precisares de mexer no
backend para o RPi funcionar, algo no contrato ficou mal definido — revê a
secção 18 do `DECISOES_LOCAIS.md`.

---

## 7) Veredito rápido "está no melhor que podia estar?"

Coisas que eu marcaria como **sólidas**: desacoplamento publisher/subscriber,
reutilização do pipeline existente, durabilidade (mensagens persistentes + acks
manuais + queue/exchange durables), reconexão automática, e o contrato de
mensagem alinhado com o `SensorIngestRequest` que já existia.

Coisas que eu **reavaliaria** antes de considerar "fechado": credenciais de rede
(ainda `guest/guest`), gestão de env vars/`.env`, ausência de testes
automatizados, e a decisão sobre retry do consumer se o broker estiver em baixo
no arranque. Nenhuma destas bloqueia a fase do RPi, mas valem revisão.
