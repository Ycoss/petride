# PetRide

Aplicación de viajes para mascotas que usa Redis Cloud como base de datos clave-valor.

Versión web: https://petride.streamlit.app/

## Requerimientos

- Python 3.10+
- Base de datos en Redis Cloud

## Instalación

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Poner en `.env` la URL de conexión de Redis Cloud.

## Ejecución

```bash
python seed.py
python app.py
```

`seed.py` solo carga datos si la base está vacía. Para borrar todo y volver a los datos de prueba:

```bash
python seed.py --reset
```

Versión web:

```bash
streamlit run web.py
```

## Archivos

- `config.py` conexión a Redis
- `models.py` modelos Mascota, Chofer y Viaje (redis-om)
- `operacion.py` choferes en línea, solicitudes y viajes
- `app.py` menú en terminal
- `web.py` interfaz web
- `seed.py` datos iniciales
- `docs/` documento del proyecto

## Claves

| Clave | Tipo | TTL |
|---|---|---|
| `petride:mascota:<pk>` | hash | - |
| `petride:chofer:<pk>` | hash | - |
| `petride:viaje:<pk>` | hash | - |
| `petride:online:<pk>` | string | 60 s |
| `petride:jaulas:<pk>` | string | - |
| `petride:folio` | string | - |
| `petride:solicitud:<folio>` | hash | 120 s |
| `petride:completados` | string | - |

## Comandos en la terminal

Requiere `redis-cli` (en Mac: `brew install redis`). La contraseña no se escribe: se toma del `.env`.

Conectarse a Redis Cloud:

```bash
source .env
redis-cli -u "$REDIS_URL" --no-auth-warning
```

Dentro de `redis-cli`:

```
PING                                   # responde PONG si hay conexión
KEYS petride:*                         # lista las claves del proyecto
HGETALL petride:mascota:<pk>           # ver una mascota (hash)
HGET petride:mascota:<pk> nombre       # ver un solo campo
TYPE petride:mascota:<pk>              # tipo de dato (hash)
HGETALL petride:solicitud:<folio>      # ver una solicitud de viaje
GET petride:folio                      # ultimo folio
GET petride:completados                # viajes completados
GET petride:online:<pk>                # zona del chofer, (nil) si ya expiro
TTL petride:solicitud:<folio>          # segundos que le quedan
SET petride:prueba hola EX 30          # crear una clave con ttl de 30 s
INCR petride:prueba:contador           # contador atomico
DEL petride:prueba petride:prueba:contador
EXIT
```

Desde Python:

```bash
python seed.py            # carga datos si la base esta vacia
python seed.py --reset    # borra y vuelve a cargar los datos de prueba
python app.py             # menu en terminal
streamlit run web.py      # version web local
```
