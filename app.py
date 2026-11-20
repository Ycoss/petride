# menu de terminal de petride
from redis_om import Migrator
from models import Mascota, Chofer, Viaje
from config import redis_conn as r
import operacion as op

Migrator().run()  # indices para .find()


def escoger(lista):
    for i, texto in enumerate(lista, 1):
        print(f"  {i}. {texto}")
    opcion = input("Número: ")
    if opcion.isdigit() and 1 <= int(opcion) <= len(lista):
        return int(opcion) - 1
    return None


def mostrar_mascotas():
    mascotas = Mascota.find().all()
    i = escoger([f"{m.nombre} ({m.especie}, {m.tamano}, {m.peso_kg} kg) - dueño: {m.dueno}" for m in mascotas])
    return mascotas[i] if i is not None else None


while True:
    print("\n===== PETRIDE: viajes para mascotas =====")
    print("1. Registrar mascota       6. Conectar chofer (60 s)")
    print("2. Ver mascotas            7. Solicitar viaje")
    print("3. Actualizar peso         8. Atender solicitud")
    print("4. Eliminar mascota        9. Completar viaje")
    print("5. Buscar por especie     10. Historial")
    print("0. Salir")
    opcion = input("> ")

    if opcion == "1":  # create
        mascota = Mascota(nombre=input("Nombre: "), especie=input("Especie: "),
                          tamano=input("Tamaño (chico/mediano/grande): "),
                          peso_kg=float(input("Peso kg: ")), dueno=input("Dueño: "))
        mascota.save()
        print("Guardada con pk:", mascota.pk)

    elif opcion == "2":  # read
        for m in Mascota.find().all():
            print(m.model_dump())

    elif opcion == "3":  # update
        mascota = mostrar_mascotas()
        if mascota:
            mascota.peso_kg = float(input("Nuevo peso kg: "))
            mascota.save()
            print("Actualizada.")

    elif opcion == "4":  # delete
        mascota = mostrar_mascotas()
        if mascota:
            Mascota.delete(mascota.pk)
            print("Eliminada.")

    elif opcion == "5":  # busqueda con find
        especie = input("Especie: ")
        for m in Mascota.find(Mascota.especie == especie).all():
            print(f"- {m.nombre} ({m.peso_kg} kg)")

    elif opcion == "6":  # set + expire
        choferes = Chofer.find().all()
        i = escoger([f"{c.nombre} - zona {c.zona} - {'EN LÍNEA' if op.esta_en_linea(c) else 'fuera'}"
                     for c in choferes])
        if i is not None:
            op.conectar_chofer(choferes[i])
            print(f"{choferes[i].nombre} en línea por {op.TTL_CHOFER} s.")

    elif opcion == "7":  # incr + hset + expire
        mascota = mostrar_mascotas()
        if mascota:
            folio = op.solicitar_viaje(mascota, input("Destino: "), float(input("Cuánto ofreces $: ")))
            print(f"Solicitud {folio} creada. Expira en {op.TTL_SOLICITUD} s si nadie la acepta.")

    elif opcion == "8":  # aceptar, contraofertar o declinar
        pendientes = [s for s in op.ver_solicitudes() if s["estado"] in ("solicitado", "contraoferta")]
        i = escoger([f"Folio {s['folio']}: {s['mascota']} -> {s['destino']} (${s['tarifa']}) {s['estado']}"
                     for s in pendientes])
        if i is None:
            continue
        s = pendientes[i]
        if s["estado"] == "contraoferta":
            if input(f"{s['chofer']} pide ${s['contraoferta']}. ¿Aceptas? (s/n): ") == "s":
                if op.aceptar_viaje(s["folio"], Chofer.get(s["chofer_pk"])):
                    print("Viaje aceptado.")
            else:
                op.rechazar_contraoferta(s["folio"])
                print("Contraoferta rechazada.")
            continue
        en_linea = [c for c in Chofer.find().all() if op.esta_en_linea(c)]
        print("Chofer en línea:")
        j = escoger([c.nombre for c in en_linea])
        if j is None:
            continue
        decision = input("a) aceptar  c) contraofertar  d) declinar: ")
        if decision == "a" and op.aceptar_viaje(s["folio"], en_linea[j]):
            print("Viaje aceptado.")
        elif decision == "c":
            op.contraofertar(s["folio"], en_linea[j], float(input("Nuevo precio $: ")))
            print("Contraoferta enviada al dueño.")
        elif decision == "d":
            print("Solicitud declinada.")

    elif opcion == "9":  # pasa al historial
        en_curso = [s for s in op.ver_solicitudes() if s["estado"] == "en_curso"]
        i = escoger([f"Folio {s['folio']}: {s['mascota']} con {s['chofer']}" for s in en_curso])
        if i is not None and op.completar_viaje(en_curso[i]["folio"]):
            print("Viaje completado y guardado en el historial.")

    elif opcion == "10":
        for v in Viaje.find().all():
            print(f"Folio {v.folio}: {v.mascota} -> {v.destino} | {v.chofer} | ${v.tarifa}")
        print("Viajes completados:", r.get("petride:completados") or 0)

    elif opcion == "0":
        break
