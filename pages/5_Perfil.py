"""Perfil de usuario y perfil de artista con créditos (diapositiva 9)."""
from html import escape as esc

import streamlit as st

from core import db, ui
from core.config import PLANES

user = ui.configurar_pagina("Perfil", "👤")

st.title("👤 Perfiles")

usuarios = db.listar_usuarios()
if not usuarios:
    st.info("Aún no hay usuarios.")
    st.stop()
# Artistas primero (beneficio "Primero en Destacados")
usuarios.sort(key=lambda u: (not PLANES[u["plan"]]["destacado"], u["username"]))
ids = [u["id"] for u in usuarios]
por_defecto = ids.index(user["id"]) if user and user["id"] in ids else 0
elegido = st.selectbox("Ver perfil de", usuarios, index=por_defecto,
                       format_func=lambda u: f"@{u['username']}" + (" 🎙️" if u["plan"] == "Artista" else ""))
perfil = db.usuario(elegido["id"])
propio = user is not None and perfil["id"] == user["id"]
es_artista = PLANES[perfil["plan"]]["portafolio"]

suyos = db.doblajes("d.usuario_id=? AND d.estado='activo'", (perfil["id"],), orden="votos DESC", limite=50)
creds = db.creditos(perfil["id"])

col_card, col_info = st.columns([2, 3], gap="large")
with col_card:
    lineas_cred = "<br>".join(
        f"{esc(c['obra'])} — {esc(c['idioma'])} {'✓' if c['verificado'] else '<i>(por verificar)</i>'}" for c in creds
    ) or "<i>Sin créditos todavía</i>"
    destacadas = " · ".join(esc(d['titulo']) for d in suyos[:3]) or "<i>Sin escenas</i>"
    ui.tarjeta(
        f"{esc(perfil['nombre'])} <small>@{esc(perfil['username'])}</small>",
        f"{ui.insignia_html(perfil['plan'])}<p>{esc(perfil['bio'] or '')}</p>"
        + (f"<p><b>CRÉDITOS</b><br>{lineas_cred}</p>" if es_artista else "")
        + f"<p><b>ESCENAS DESTACADAS</b><br>{destacadas}</p>",
        oscura=es_artista,
    )
    total_votos = sum(d["votos"] for d in suyos)
    m1, m2 = st.columns(2)
    m1.metric("Doblajes", len(suyos))
    m2.metric("Votos recibidos", total_votos)

with col_info:
    if propio:
        with st.expander("✏️ Editar mi perfil", expanded=not perfil["bio"]):
            with st.form("perfil"):
                nombre = st.text_input("Nombre artístico", perfil["nombre"])
                bio = st.text_area("Bio", perfil["bio"], max_chars=300)
                if st.form_submit_button("Guardar"):
                    db.actualizar_perfil(perfil["id"], nombre, bio)
                    st.rerun()
        if es_artista:
            with st.expander("🎬 Agregar crédito profesional"):
                st.caption("Se verifica con contrato, ficha de doblaje o confirmación del estudio.")
                with st.form("credito", clear_on_submit=True):
                    obra = st.text_input("Película, serie o anime")
                    idioma = st.text_input("Idioma / versión", "Español latino")
                    if st.form_submit_button("Enviar a verificación") and obra.strip():
                        db.agregar_credito(perfil["id"], obra.strip(), idioma.strip())
                        st.rerun()
        else:
            st.info("Con el plan **Artista** tienes portafolio con créditos y apareces primero en Destacados.")
            st.page_link("pages/6_Planes.py", label="Ver planes", icon="💳")

    st.subheader("🔊 Escucha su voz")
    if not suyos:
        st.caption("Todavía no hay doblajes.")
    mis_votos = db.votos_de(user["id"]) if user else set()
    for d in suyos[:6]:
        ui.tarjeta_doblaje(d, user, mis_votos, prefijo="perf")
