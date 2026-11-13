"""Estudio en el navegador: eliges un fragmento (escena, un minuto o a medida) y grabas tu voz."""
import streamlit as st

from core import db, ui
from core.config import MARGEN_GRABACION, PLANES, UMBRAL_PISTA, VARIANTES

user = ui.requiere_usuario(ui.configurar_pagina("Estudio", "🎙️"))
plan = PLANES[user["plan"]]
max_plan = plan["max_seg"]  # None = ilimitado

st.title("🎙️ Estudio de doblaje")
limite_txt = "ilimitada" if max_plan is None else f"hasta {ui.fmt_tiempo(max_plan)}"
st.caption(f"Tu plan **{user['plan']}** permite doblajes de duración {limite_txt}. "
           f"Si tu doblaje junta {UMBRAL_PISTA} votos, queda como pista seleccionable en «Ver con pistas».")

if publicado := st.session_state.pop("estudio_publicado", None):
    st.success("¡Doblaje guardado! Así queda sobre el video:")
    d = db.doblaje(publicado)
    ui.reproductor(d["video_url"], d["inicio"], d["fin"], d["audio_path"], alto=420)
    st.divider()

lista_obras = db.obras()
if not lista_obras:
    st.error("El catálogo está vacío.")
    st.stop()

# --------------------------------------------------------- elegir fragmento
c1, c2 = st.columns(2)
obra = c1.selectbox("Obra", lista_obras, format_func=lambda o: f"{o['obra']} ({o['tipo']})")
modo = c2.radio("¿Qué quieres doblar?", ["Escena del catálogo", "Un minuto", "Fragmento a medida"],
                horizontal=True)

escenas_obra = [e for e in db.escenas() if e["obra"] == obra["obra"]]
tope = max_plan if max_plan is not None else 30 * 60  # tope práctico de la interfaz: 30 min

if modo == "Escena del catálogo":
    esc = st.selectbox("Escena", escenas_obra,
                       format_func=lambda e: f"{e['titulo']} ({ui.fmt_tiempo(e['inicio'])})")
    escena_id, inicio, fin = esc["id"], esc["inicio"], esc["fin"]
else:
    escena_id = escenas_obra[0]["id"]
    a, b = st.columns(2)
    inicio = a.number_input("Empieza en (segundos)", min_value=0, value=0, step=5)
    if modo == "Un minuto":
        duracion = 60
        b.metric("Duración", "1:00")
    else:
        duracion = b.slider("Duración (segundos)", 10, max(10, tope), min(60, tope), step=5)
    fin = inicio + duracion

dur_fragmento = fin - inicio
if max_plan is not None and dur_fragmento > max_plan:
    st.error(f"Ese fragmento dura {ui.fmt_tiempo(dur_fragmento)} y tu plan permite {ui.fmt_tiempo(max_plan)}.")
    st.page_link("pages/6_Planes.py", label="Mejorar plan", icon="💳")
    st.stop()

# --------------------------------------------------------------- grabación
col_v, col_g = st.columns([3, 2], gap="large")
with col_v:
    silenciar = st.toggle("Silenciar el audio original", value=True)
    st.video(obra["video_url"], start_time=int(inicio), end_time=int(fin), muted=silenciar)
    st.caption(f"Fragmento {ui.fmt_tiempo(inicio)} – {ui.fmt_tiempo(fin)} · {obra['licencia']}")

with col_g:
    espera = ui.segundos_de_espera(user)
    if espera:
        st.warning(f"⏳ Podrás publicar otro doblaje en {ui.fmt_tiempo(espera)} (tiempo de espera del plan).")
    variante = st.selectbox("Variante de tu doblaje", VARIANTES)
    st.session_state.setdefault("estudio_n", 0)
    n = st.session_state["estudio_n"]
    t1, t2 = st.tabs(["Grabar aquí", "Subir archivo"])
    with t1:
        st.caption("Dale play al video y graba a la vez. Usa audífonos.")
        grabado = t1.audio_input("Micrófono", key=f"emic{n}")
    with t2:
        subido = t2.file_uploader("Audio (wav, mp3, m4a, ogg)", type=["wav", "mp3", "m4a", "ogg"], key=f"eup{n}")

    audio = grabado or subido
    if audio:
        datos = audio.getvalue()
        ext = "wav" if grabado else audio.name.rsplit(".", 1)[-1].lower()
        dur = ui.duracion_audio(datos)
        if dur is None:
            st.error("No pude leer la duración del audio. Prueba con WAV o MP3.")
        elif dur > dur_fragmento + MARGEN_GRABACION:
            st.error(f"Tu audio ({dur:.1f} s) es más largo que el fragmento ({dur_fragmento} s).")
        else:
            st.success(f"Audio listo: {dur:.1f} s")
            if st.button("💾 Guardar doblaje", type="primary", width="stretch", disabled=bool(espera)):
                did = db.guardar_doblaje(user["id"], escena_id, "estudio", None, variante,
                                         int(inicio), int(fin), datos, dur, ext)
                st.session_state["estudio_n"] += 1
                st.session_state["estudio_publicado"] = did
                st.rerun()
