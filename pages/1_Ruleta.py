"""Modo competencia: Gira → Graba → Vota → Ranking (diapositiva 6)."""
import random
import time

import streamlit as st

from core import db, ui
from core.config import CATEGORIAS, DURACION_RULETA, MARGEN_GRABACION, VARIANTES

user = ui.requiere_usuario(ui.configurar_pagina("Ruleta", "🎰"))

st.title("🎰 Modo competencia: la ruleta")
st.caption("1 Gira · 2 Graba · 3 Vota · 4 Ranking semanal por categorías")

espera = ui.segundos_de_espera(user)
if espera:
    st.warning(f"⏳ Tu plan **{user['plan']}** tiene tiempo de espera entre doblajes. "
               f"Podrás grabar de nuevo en {ui.fmt_tiempo(espera)}.")
    st.page_link("pages/6_Planes.py", label="Ver planes sin espera", icon="💳")

st.session_state.setdefault("ruleta_n", 0)

# ------------------------------------------------- resultado tras publicar
if did := st.session_state.pop("ruleta_publicado", None):
    st.balloons()
    st.success("¡Publicado! Ahora la comunidad vota. Así suena tu doblaje:")
    d = db.doblaje(did)
    ui.reproductor(d["video_url"], d["inicio"], d["fin"], d["audio_path"])
    st.page_link("pages/3_Votar_y_ranking.py", label="Ir a votar y ver el ranking", icon="🗳️")
    st.divider()

# ------------------------------------------------------------------ 1. Gira
if st.button("🎰 ¡Girar la ruleta!", type="primary", width="stretch"):
    catalogo = db.escenas()
    if not catalogo:
        st.error("No hay escenas activas en el catálogo.")
        st.stop()
    with st.spinner("Girando…"):
        time.sleep(0.8)
    anterior = st.session_state.get("ruleta_escena")
    opciones = [e for e in catalogo if e["id"] != anterior] or catalogo
    st.session_state["ruleta_escena"] = random.choice(opciones)["id"]

esc_id = st.session_state.get("ruleta_escena")
if not esc_id:
    ui.banda("2 CATEGORÍAS", "Mejor doblaje y Desastre más glorioso: el humor también gana.")
    st.stop()

esc = db.escena(esc_id)
st.subheader(f"🎬 {esc['obra']} — {esc['titulo']}")
st.caption(f"{esc['tipo']} · {ui.fmt_tiempo(esc['inicio'])}–{ui.fmt_tiempo(esc['fin'])} · Licencia: {esc['licencia']}")

col_video, col_grabar = st.columns([3, 2], gap="large")
with col_video:
    silenciar = st.toggle("Ver la escena sin sonido (para practicar)", value=False)
    st.video(esc["video_url"], start_time=esc["inicio"], end_time=esc["fin"], muted=silenciar)
    st.caption("🎧 Usa audífonos al grabar para que el micrófono no capte el audio original.")

# ------------------------------------------------------------------ 2. Graba
with col_grabar:
    st.markdown("#### 🎙️ Tu doblaje")
    categoria = st.radio("¿En qué categoría compites?", list(CATEGORIAS),
                         format_func=CATEGORIAS.get, horizontal=True)
    variante = st.selectbox("Variante", VARIANTES)
    n = st.session_state["ruleta_n"]
    tab_mic, tab_archivo = st.tabs(["Grabar aquí", "Subir archivo"])
    with tab_mic:
        grabado = st.audio_input("Graba mientras ves la escena", key=f"mic{n}")
    with tab_archivo:
        subido = st.file_uploader("Audio (wav, mp3, m4a, ogg)", type=["wav", "mp3", "m4a", "ogg"], key=f"up{n}")

    audio = grabado or subido
    if audio:
        datos = audio.getvalue()
        ext = "wav" if grabado else audio.name.rsplit(".", 1)[-1].lower()
        dur = ui.duracion_audio(datos)
        limite = DURACION_RULETA + MARGEN_GRABACION
        if dur is None:
            st.error("No pude leer la duración del audio. Prueba con WAV o MP3.")
        elif dur > limite:
            st.error(f"Tu audio dura {dur:.1f} s. En la ruleta el máximo es {limite} s.")
        else:
            st.success(f"Audio listo: {dur:.1f} s")
            if st.button("🚀 Publicar en la competencia", type="primary", width="stretch",
                         disabled=bool(espera)):
                did = db.guardar_doblaje(user["id"], esc["id"], "ruleta", categoria, variante,
                                         esc["inicio"], esc["fin"], datos, dur, ext)
                st.session_state["ruleta_n"] += 1
                st.session_state["ruleta_publicado"] = did
                st.session_state.pop("ruleta_escena", None)
                st.rerun()
