# version web
import io
from contextlib import redirect_stdout

import streamlit as st
from redis_om import Migrator

import operacion as op
from config import redis_conn as r
from models import Chofer, Mascota, Viaje

st.set_page_config(page_title="PetRide", page_icon=":material/pets:", layout="wide")


@st.cache_resource
def preparar_indices():
    Migrator().run()
    return True


preparar_indices()


def avisar(funcion, *args, exito=""):
    salida = io.StringIO()
    with redirect_stdout(salida):
        ok = funcion(*args)
    if ok:
        st.session_state["aviso"] = exito
        st.rerun()
    st.warning(salida.getvalue().strip())


st.title(":material/pets: PetRide")
st.caption("Redis Cloud: " + ("conectado" if r.ping() else "sin conexión"))
if "aviso" in st.session_state:
    st.success(st.session_state.pop("aviso"))

inicio, mascotas_tab, choferes_tab, viajes_tab, historial_tab = st.tabs(
    [":material/monitoring: En vivo", ":material/pets: Mascotas", ":material/local_taxi: Choferes", ":material/route: Viajes", ":material/receipt_long: Historial"])

# se refresca cada 5 s
with inicio:
    @st.fragment(run_every=5)
    def panel():
        en_linea = [c for c in Chofer.find().all() if op.esta_en_linea(c)]
        solicitudes = op.ver_solicitudes()
        a, b, c = st.columns(3)
        a.metric("Choferes en línea", len(en_linea))
        b.metric("Solicitudes activas", len(solicitudes))
        c.metric("Viajes completados", r.get("petride:completados") or 0)
        izq, der = st.columns(2)
        izq.subheader(":material/person_pin_circle: Choferes en línea")
        izq.dataframe([{"Chofer": ch.nombre, "Zona": ch.zona,
                        "Jaulas libres": int(r.get(f"petride:jaulas:{ch.pk}") or 0)} for ch in en_linea],
                      hide_index=True, width="stretch")
        der.subheader(":material/pending_actions: Solicitudes activas")
        der.dataframe(solicitudes, hide_index=True, width="stretch")

    panel()

# crud de mascotas
with mascotas_tab:
    mascotas = Mascota.find().all()
    st.dataframe([m.model_dump() for m in mascotas], hide_index=True, width="stretch")
    crear, editar, buscar = st.columns(3)
    with crear.form("crear", clear_on_submit=True):
        st.markdown("**:material/add: Registrar mascota**")
        nombre = st.text_input("Nombre")
        especie = st.selectbox("Especie", ["perro", "gato", "ave", "conejo", "otro"])
        tamano = st.selectbox("Tamaño", ["chico", "mediano", "grande"])
        peso = st.number_input("Peso (kg)", min_value=0.0, step=0.5)
        dueno = st.text_input("Dueño")
        if st.form_submit_button("Guardar") and nombre:
            Mascota(nombre=nombre, especie=especie, tamano=tamano, peso_kg=peso, dueno=dueno).save()
            st.session_state["aviso"] = f"{nombre} registrada."
            st.rerun()
    with editar:
        st.markdown("**:material/edit: Actualizar o eliminar**")
        if mascotas:
            m = st.selectbox("Mascota", mascotas, format_func=lambda x: x.nombre)
            nuevo_peso = st.number_input("Peso (kg)", value=float(m.peso_kg), step=0.5, key=m.pk)
            if st.button("Actualizar peso"):
                m.peso_kg = nuevo_peso
                m.save()
                st.rerun()
            if st.button("Eliminar", type="primary"):
                Mascota.delete(m.pk)
                st.rerun()
    with buscar:
        st.markdown("**:material/search: Buscar por especie**")
        especie = st.selectbox("Especie", ["perro", "gato", "ave", "conejo", "otro"], key="buscar")
        for m in Mascota.find(Mascota.especie == especie).all():
            st.write(f"- {m.nombre} ({m.peso_kg} kg)")

# choferes
with choferes_tab:
    choferes = Chofer.find().all()
    st.dataframe([{"En línea": "sí" if op.esta_en_linea(c) else "no", "Nombre": c.nombre,
                   "Vehículo": c.vehiculo, "Zona": c.zona, "Jaulas": c.jaulas} for c in choferes],
                 hide_index=True, width="stretch")
    chofer = st.selectbox("Chofer", choferes, format_func=lambda c: c.nombre)
    if st.button(f"Conectar por {op.TTL_CHOFER} s", icon=":material/wifi:"):
        op.conectar_chofer(chofer)
        st.session_state["aviso"] = f"{chofer.nombre} en línea por {op.TTL_CHOFER} s."
        st.rerun()

# viajes
with viajes_tab:
    solicitar, aceptar, completar = st.columns(3)
    with solicitar.form("solicitar", clear_on_submit=True):
        st.markdown("**:material/add_location: Solicitar viaje**")
        mascota = st.selectbox("Mascota", Mascota.find().all(), format_func=lambda m: m.nombre)
        destino = st.text_input("Destino")
        oferta = st.number_input("Cuánto ofreces ($)", min_value=0.0, step=10.0)
        if st.form_submit_button("Solicitar") and mascota and destino:
            folio = op.solicitar_viaje(mascota, destino, oferta)
            st.session_state["aviso"] = f"Solicitud {folio} creada. Expira en {op.TTL_SOLICITUD} s."
            st.rerun()

    solicitudes = op.ver_solicitudes()
    with aceptar:
        st.markdown("**:material/local_taxi: Atender solicitud**")
        pendientes = [s for s in solicitudes if s["estado"] in ("solicitado", "contraoferta")]
        en_linea = [c for c in Chofer.find().all() if op.esta_en_linea(c)]
        if pendientes:
            s = st.selectbox("Solicitud", pendientes,
                             format_func=lambda s: f"#{s['folio']} {s['mascota']} ${s['tarifa']} ({s['estado']})")
            if s["estado"] == "contraoferta":
                st.write(f"{s['chofer']} pide ${s['contraoferta']}")
                if st.button("Aceptar contraoferta"):
                    avisar(op.aceptar_viaje, s["folio"], Chofer.get(s["chofer_pk"]), exito="Viaje aceptado.")
                if st.button("Rechazar"):
                    op.rechazar_contraoferta(s["folio"])
                    st.rerun()
            elif en_linea:
                c = st.selectbox("Chofer en línea", en_linea, format_func=lambda c: c.nombre)
                monto = st.number_input("Contraoferta ($)", min_value=0.0, step=10.0, value=float(s["tarifa"]))
                a1, a2, a3 = st.columns(3)
                if a1.button("Aceptar"):
                    avisar(op.aceptar_viaje, s["folio"], c, exito=f"Viaje #{s['folio']} aceptado por {c.nombre}.")
                if a2.button("Contraofertar"):
                    op.contraofertar(s["folio"], c, monto)
                    st.rerun()
                if a3.button("Declinar"):
                    st.session_state["aviso"] = f"{c.nombre} declinó el viaje #{s['folio']}."
                    st.rerun()
            else:
                st.info("Conecta un chofer para atender la solicitud.")
        else:
            st.info("No hay solicitudes pendientes.")
    with completar:
        st.markdown("**:material/task_alt: Completar viaje**")
        en_curso = [s for s in solicitudes if s["estado"] == "en_curso"]
        if en_curso:
            s = st.selectbox("Viaje", en_curso, format_func=lambda s: f"#{s['folio']} {s['mascota']} con {s['chofer']}")
            if st.button("Completar"):
                avisar(op.completar_viaje, s["folio"], exito=f"Viaje #{s['folio']} completado.")
        else:
            st.info("No hay viajes en curso.")

# historial
with historial_tab:
    viajes = Viaje.find().all()
    st.metric("Ingresos", f"${sum(v.tarifa for v in viajes):,.2f}")
    st.dataframe([v.model_dump() for v in viajes], hide_index=True, width="stretch")
