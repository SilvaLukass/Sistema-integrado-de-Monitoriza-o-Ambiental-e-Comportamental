# Decisoes locais

## RPi sensors + camera (2026-06-09)

### Transporte
- **Telemetria (sensores):** RabbitMQ topic exchange `eldercare.sensors`, routing key `sensors.rpi`.
- **Camera (frame unico):** HTTP request/reply (`POST /capture` no RPi, proxy no backend).

### Mapeamento sensores -> payload
| Sensor real | Chave | Notas |
|---|---|---|
| Reed switch (porta) | `D001` | 0 fechada, 1 aberta |
| DHT22 temperatura | `T001` | graus Celsius |
| DHT22 humidade | `H001` | guardada na BD, ignorada pelo modelo |

### RabbitMQ credenciais LAN
- O user `guest` so funciona em `localhost`.
- `docker-compose.yml` usa `eldercare` / `eldercare_dev`.
- Backend e agente RPi devem apontar para `amqp://eldercare:eldercare_dev@<BROKER_IP>:5672/`.

### Camera e privacidade
- Um unico frame por pedido explicito (dashboard ou Telegram).
- O backend nao persiste JPEGs; apenas faz proxy em memoria.
- Alertas `danger` no Telegram incluem botoes Sim/Nao para pedir frame.
