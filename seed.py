# carga datos de prueba, solo si la base esta vacia o con --reset
import sys
from redis_om import Migrator
from models import Mascota, Chofer, Viaje
from config import redis_conn as r
import operacion as op

Migrator().run()

if Mascota.find().all() and "--reset" not in sys.argv:
    print("ya hay datos, para reiniciar usa: python seed.py --reset")
    sys.exit()

# limpiar datos anteriores
for chofer in Chofer.find().all():
    r.delete(f"petride:online:{chofer.pk}", f"petride:jaulas:{chofer.pk}")
for folio in range(1, int(r.get("petride:folio") or 0) + 1):
    r.delete(f"petride:solicitud:{folio}")
r.delete("petride:folio", "petride:completados")
for modelo in [Mascota, Chofer, Viaje]:
    for objeto in modelo.find().all():
        modelo.delete(objeto.pk)

# mascotas y choferes
firulais = Mascota(nombre="Firulais", especie="perro", tamano="grande", peso_kg=32.5, dueno="Ana").save()
Mascota(nombre="Michi", especie="gato", tamano="chico", peso_kg=4.2, dueno="Ana").save()
Mascota(nombre="Rocky", especie="perro", tamano="mediano", peso_kg=12.0, dueno="Luis").save()
copito = Mascota(nombre="Copito", especie="conejo", tamano="chico", peso_kg=1.8, dueno="Sofía").save()

carlos = Chofer(nombre="Carlos", vehiculo="Nissan NV200", zona="Centro", jaulas=3).save()
Chofer(nombre="María", vehiculo="Kia Soul", zona="Norte", jaulas=2).save()
Chofer(nombre="Paola", vehiculo="Honda Fit", zona="Sur", jaulas=1).save()

# un viaje completado y una solicitud pendiente
op.conectar_chofer(carlos)
folio = op.solicitar_viaje(firulais, "Veterinaria Patitas", 150)
op.aceptar_viaje(folio, carlos)
op.completar_viaje(folio)
op.solicitar_viaje(copito, "Estética Canina", 90)

print("datos cargados")
