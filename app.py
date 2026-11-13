"""DoblaVerso — página de inicio.  Ejecutar con:  streamlit run app.py"""
import streamlit as st

from core import db, ui
from core.config import PLANES

user = ui.configurar_pagina("Inicio")

st.markdown("""
<div class="dv-hero">
  <div class="dv-kicker">DOBLAJE HECHO POR LA COMUNIDAD</div>
  <h1>DoblaVerso</h1>
  <p>Ver, doblar y competir: la desastrosa perfección del doblaje hecho por la comunidad.</p>
</div>
""", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
with c1:
    ui.tarjeta("📺 Ver", "Escenas con su audio original o con pistas creadas y votadas por la comunidad.")
    st.page_link("pages/4_Ver_con_pistas.py", label="Ir a Ver", icon="➡️")
with c2:
    ui.tarjeta("🎙️ Doblar", "Estudio en el navegador: eliges un fragmento y grabas tu voz encima.")
    st.page_link("pages/2_Estudio.py", label="Ir al Estudio", icon="➡️")
with c3:
    ui.tarjeta("🎰 Competir", "Escenas al azar de 30 segundos. Gana el mejor doblaje… o el más desastroso.",
               oscura=True)
    st.page_link("pages/1_Ruleta.py", label="Girar la ruleta", icon="➡️")

st.divider()
s = db.estadisticas()
m1, m2, m3, m4 = st.columns(4)
m1.metric("Usuarios", s["usuarios"])
m2.metric("Doblajes", s["doblajes"])
m3.metric("Votos", s["votos"])
m4.metric("Escenas disponibles", s["escenas"])

# Destacados: los artistas aparecen primero (beneficio del plan Artista)
st.subheader("⭐ Destacados de la comunidad")
recientes = db.doblajes("d.estado='activo'", orden="votos DESC, d.creado DESC", limite=12)
recientes.sort(key=lambda d: (not PLANES[d["plan_autor"]]["destacado"], -d["votos"]))
if not recientes:
    st.info("Todavía no hay doblajes. ¡Sé el primero en girar la ruleta!")
else:
    mis_votos = db.votos_de(user["id"]) if user else set()
    cols = st.columns(2)
    for i, d in enumerate(recientes[:4]):
        with cols[i % 2]:
            ui.tarjeta_doblaje(d, user, mis_votos, prefijo="home")

ui.banda("REGLA DE ORO", "No alojamos ni enlazamos episodios sin licencia. "
         "Este MVP usa solo películas abiertas (Creative Commons) y guarda únicamente el audio.")
