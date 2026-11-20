# modelos de redis-om, cada objeto se guarda como hash
from redis_om import HashModel, Field
from config import redis_conn


class Mascota(HashModel, index=True):
    nombre: str
    especie: str = Field(index=True)
    tamano: str
    peso_kg: float = Field(index=True)
    dueno: str = Field(index=True)

    class Meta:
        database = redis_conn
        global_key_prefix = "petride"
        model_key_prefix = "mascota"


class Chofer(HashModel, index=True):
    nombre: str
    vehiculo: str
    zona: str = Field(index=True)
    jaulas: int

    class Meta:
        database = redis_conn
        global_key_prefix = "petride"
        model_key_prefix = "chofer"


# historial de viajes, no expira
class Viaje(HashModel, index=True):
    folio: int
    mascota: str
    chofer: str = Field(index=True)
    destino: str
    tarifa: float

    class Meta:
        database = redis_conn
        global_key_prefix = "petride"
        model_key_prefix = "viaje"
