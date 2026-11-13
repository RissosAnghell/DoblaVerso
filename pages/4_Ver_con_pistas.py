"""Reproductor con selector de pista de audio (diapositiva 7)."""
import streamlit as st

from core import db, ui
from core.config import UMBRAL_PISTA

user = ui.configurar_pagina("Ver con pistas", "📺")

st.title("📺 Ver con pistas de la comunidad")
st.caption(f"Cuando un doblaje junta {UMBRAL_PISTA} votos queda como pista seleccionable, "
           "igual que un idioma oficial. El video no se toca: solo cambia el audio.")

lista_obras = db.obras()
if not lista_obras:
    st.stop()
obra = st.selectbox("¿Qué quieres ver?", lista_obras, format_func=lambda o: f"{o['obra']} ({o['tipo']})")
pistas = db.pistas_de_obra(obra["obra"])

col_player, col_pistas = st.columns([3, 2], gap="large")
with col_pistas:
    st.markdown("##### PISTA DE AUDIO")
    opciones = [None, *pistas]

    def etiqueta(p):
        if p is None:
            return "Original · Oficial"
        estrella = "★ " if p is pistas[0] else ""
        return (f"{estrella}{p['variante']} · Comunidad — @{p['username']} "
                f"({ui.fmt_tiempo(p['inicio'])}, {p['votos']} votos)")

    elegida = st.radio("Pista", opciones, format_func=etiqueta, label_visibility="collapsed")
    if not pistas:
        st.info("Esta obra aún no tiene pistas de comunidad. ¡Dobla una escena en el Estudio o en la Ruleta!")

with col_player:
    if elegida is None:
        st.video(obra["video_url"])
        st.caption(obra["licencia"])
    else:
        ui.reproductor(obra["video_url"], elegida["inicio"], elegida["fin"], elegida["audio_path"], alto=440)
        st.caption(f"Doblaje de @{elegida['username']} · {elegida['variante']} · {obra['licencia']}")

# Doblajes que todavía no llegan al umbral
candidatos = [d for d in db.doblajes("e.obra=? AND d.estado='activo'", (obra["obra"],), orden="votos DESC")
              if d["votos"] < UMBRAL_PISTA]
if candidatos:
    st.divider()
    st.subheader("🗳️ Candidatas a pista")
    st.caption("Vota para que se vuelvan pistas seleccionables.")
    mis_votos = db.votos_de(user["id"]) if user else set()
    cols = st.columns(2)
    for i, d in enumerate(candidatos[:6]):
        with cols[i % 2]:
            st.progress(d["votos"] / UMBRAL_PISTA, text=f"{d['votos']}/{UMBRAL_PISTA} votos")
            ui.tarjeta_doblaje(d, user, mis_votos, prefijo="cand")
