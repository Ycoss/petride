# viajes en tiempo real (set, hset, expire, incr, decr)
from config import redis_conn as r
from models import Viaje

TTL_CHOFER = 60
TTL_SOLICITUD = 120


def conectar_chofer(chofer):
    r.set(f"petride:online:{chofer.pk}", chofer.zona)
    r.expire(f"petride:online:{chofer.pk}", TTL_CHOFER)
    if r.get(f"petride:jaulas:{chofer.pk}") is None:
        r.set(f"petride:jaulas:{chofer.pk}", chofer.jaulas)


def esta_en_linea(chofer):
    return r.get(f"petride:online:{chofer.pk}") is not None


def solicitar_viaje(mascota, destino, oferta):
    folio = r.incr("petride:folio")
    clave = f"petride:solicitud:{folio}"
    r.hset(clave, mapping={"folio": folio, "estado": "solicitado", "mascota": mascota.nombre,
                           "destino": destino, "tarifa": oferta})
    r.expire(clave, TTL_SOLICITUD)
    return folio


def ver_solicitudes():
    solicitudes = []
    for folio in range(1, int(r.get("petride:folio") or 0) + 1):
        datos = r.hgetall(f"petride:solicitud:{folio}")
        if datos:
            solicitudes.append(datos)
    return solicitudes


# el chofer propone otro precio y el dueño decide
def contraofertar(folio, chofer, monto):
    r.hset(f"petride:solicitud:{folio}", mapping={"estado": "contraoferta", "contraoferta": monto,
                                                 "chofer": chofer.nombre, "chofer_pk": chofer.pk})


def rechazar_contraoferta(folio):
    r.hset(f"petride:solicitud:{folio}", "estado", "solicitado")


def aceptar_viaje(folio, chofer):
    clave = f"petride:solicitud:{folio}"
    estado = r.hget(clave, "estado")
    if estado not in ("solicitado", "contraoferta"):
        print("La solicitud ya expiró o ya fue tomada.")
        return False
    # decr es atomico, si queda negativo no habia lugar
    if r.decr(f"petride:jaulas:{chofer.pk}") < 0:
        r.incr(f"petride:jaulas:{chofer.pk}")
        print("El chofer no tiene jaulas libres.")
        return False
    if estado == "contraoferta":
        r.hset(clave, "tarifa", r.hget(clave, "contraoferta"))
    r.hset(clave, mapping={"estado": "en_curso", "chofer": chofer.nombre, "chofer_pk": chofer.pk})
    r.expire(clave, 7200)
    return True


def completar_viaje(folio):
    clave = f"petride:solicitud:{folio}"
    datos = r.hgetall(clave)
    if datos.get("estado") != "en_curso":
        print("Solo se puede completar un viaje aceptado.")
        return False
    Viaje(folio=folio, mascota=datos["mascota"], chofer=datos["chofer"],
          destino=datos["destino"], tarifa=datos["tarifa"]).save()
    r.incr(f"petride:jaulas:{datos['chofer_pk']}")
    r.incr("petride:completados")
    r.delete(clave)
    return True
