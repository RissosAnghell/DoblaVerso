"""Panel de moderación y catálogo (plan de contingencia, diapositiva 14). Solo administradores."""
import streamlit as st

from core import db, ui
from core.config import DURACION_RULETA, TIPOS

user = ui.requiere_usuario(ui.configurar_pagina("Moderación", "🛡️"))
if not ui.es_admin(user):
    st.error("Esta página es solo para el equipo de moderación.")
    st.caption("Configura los administradores en `.streamlit/secrets.toml` (admins = \"benja,ana\") "
               "o con la variable de entorno DOBLAVERSO_ADMINS. Por defecto: usuario «admin».")
    st.stop()

st.title("🛡️ Moderación y catálogo")
t_rep, t_cred, t_cat, t_usr = st.tabs(["🚩 Reportes", "🎬 Créditos", "📚 Catálogo", "👥 Usuarios"])

# ------------------------------------------------------------------ reportes
with t_rep:
    pendientes = db.reportes_pendientes()
    if not pendientes:
        st.success("Sin reportes pendientes. 🎉")
    agrupados: dict[int, list] = {}
    for r in pendientes:
        agrupados.setdefault(r["doblaje_id"], []).append(r)
    for did, reps in agrupados.items():
        d = db.doblaje(did)
        if not d:
            continue
        with st.container(border=True):
            st.markdown(f"**{d['obra']} — {d['titulo']}** · @{d['username']} · estado: `{d['estado']}`")
            st.caption(" · ".join(f"{r['motivo']} (por @{r['reportado_por']})" for r in reps))
            ui.reproductor(d["video_url"], d["inicio"], d["fin"], d["audio_path"], alto=300, clave=f"mod{did}")
            c1, c2, c3 = st.columns(3)
            if c1.button("🗑️ Retirar", key=f"ret{did}", type="primary"):
                db.cambiar_estado_doblaje(did, "retirado"); db.resolver_reportes(did); st.rerun()
            if c2.button("✅ Mantener", key=f"man{did}"):
                db.resolver_reportes(did); st.rerun()
            if c3.button("⛔ Retirar y suspender cuenta", key=f"sus{did}"):
                db.cambiar_estado_doblaje(did, "retirado"); db.resolver_reportes(did)
                db.suspender(d["usuario_id"], True); st.rerun()

# ------------------------------------------------------------------ créditos
with t_cred:
    pend = db.creditos_pendientes()
    if not pend:
        st.success("No hay créditos por verificar.")
    for c in pend:
        a, b = st.columns([4, 1])
        a.markdown(f"@{c['username']} — **{c['obra']}** ({c['idioma']})")
        if b.button("Verificar", key=f"cr{c['id']}"):
            db.verificar_credito(c["id"], True); st.rerun()

# ------------------------------------------------------------------ catálogo
with t_cat:
    st.warning("**Regla de oro:** no alojar ni enlazar episodios sin licencia.")
    with st.form("nueva_escena", clear_on_submit=True):
        st.markdown("**Agregar escena**")
        a, b, c = st.columns(3)
        obra = a.text_input("Obra")
        titulo = b.text_input("Título de la escena")
        tipo = c.selectbox("Tipo", TIPOS)
        url = st.text_input("URL directa del video (.mp4)")
        d1, d2, d3 = st.columns(3)
        inicio = d1.number_input("Inicio (s)", min_value=0, value=0)
        fin = d2.number_input("Fin (s)", min_value=1, value=DURACION_RULETA)
        licencia = d3.text_input("Licencia", placeholder="CC BY 4.0 · Autor")
        confirmo = st.checkbox("Confirmo que tenemos licencia o que el contenido es libre/dominio público")
        if st.form_submit_button("Agregar"):
            if not (obra and titulo and url and licencia and confirmo):
                st.error("Completa todos los campos y confirma la licencia.")
            elif fin <= inicio:
                st.error("El fin debe ser mayor que el inicio.")
            elif not url.startswith(("https://", "http://")):
                st.error("La URL debe empezar con https://")
            else:
                db.agregar_escena(obra, titulo, tipo, url, int(inicio), int(fin), licencia)
                st.success("Escena agregada.")
    st.markdown("**Escenas** (desactivar = pausar el título si una distribuidora se opone)")
    for e in db.escenas(solo_activas=False):
        a, b = st.columns([5, 1])
        a.markdown(f"{'🟢' if e['activa'] else '⚪'} {e['obra']} — {e['titulo']} "
                   f"({ui.fmt_tiempo(e['inicio'])}–{ui.fmt_tiempo(e['fin'])}) · _{e['licencia']}_")
        if b.button("Pausar" if e["activa"] else "Activar", key=f"esc{e['id']}"):
            db.activar_escena(e["id"], not e["activa"]); st.rerun()

# ------------------------------------------------------------------ usuarios
with t_usr:
    for u in db.listar_usuarios():
        a, b, c = st.columns([3, 2, 1])
        a.markdown(f"@{u['username']} {'⛔' if u['suspendido'] else ''}")
        b.caption(f"Plan {u['plan']}")
        if u["id"] != user["id"] and c.button("Reactivar" if u["suspendido"] else "Suspender", key=f"u{u['id']}"):
            db.suspender(u["id"], not u["suspendido"]); st.rerun()
