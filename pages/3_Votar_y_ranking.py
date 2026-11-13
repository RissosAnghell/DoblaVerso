"""Vota la comunidad y ranking semanal por categoría."""
import streamlit as st

from core import db, ui
from core.config import CATEGORIAS, PLANES

user = ui.configurar_pagina("Votar y ranking", "🗳️")
mis_votos = db.votos_de(user["id"]) if user else set()

st.title("🗳️ Vota y ranking")
if not user:
    st.info("👈 Entra con tu usuario para votar. Igual puedes escuchar y ver el ranking.")

tab_votar, tab_ranking = st.tabs(["Votar", "🏆 Ranking semanal"])

with tab_votar:
    f1, f2, f3 = st.columns(3)
    filtro_cat = f1.selectbox("Categoría", ["Todas", *CATEGORIAS], format_func=lambda c: CATEGORIAS.get(c, c))
    filtro_modo = f2.selectbox("Origen", ["Todos", "ruleta", "estudio"],
                               format_func={"Todos": "Todos", "ruleta": "Ruleta", "estudio": "Estudio"}.get)
    orden = f3.selectbox("Ordenar por", ["Más recientes", "Más votados"])

    where, params = ["d.estado='activo'"], []
    if filtro_cat != "Todas":
        where.append("d.categoria=?"); params.append(filtro_cat)
    if filtro_modo != "Todos":
        where.append("d.modo=?"); params.append(filtro_modo)
    lista = db.doblajes(" AND ".join(where), tuple(params),
                        orden="d.creado DESC" if orden == "Más recientes" else "votos DESC, d.creado DESC",
                        limite=20)
    if user and PLANES[user["plan"]]["verificado"] is False:
        st.caption("ℹ️ Las cuentas verificadas ayudan a que los votos sean de personas reales (anti-bots).")
    if not lista:
        st.info("No hay doblajes con esos filtros todavía.")
    cols = st.columns(2)
    for i, d in enumerate(lista):
        with cols[i % 2]:
            ui.tarjeta_doblaje(d, user, mis_votos, prefijo="vot")

with tab_ranking:
    st.caption("Últimos 7 días. Lo serio y lo cómico compiten por separado.")
    c_mejor, c_desastre = st.columns(2, gap="large")
    for col, cat in ((c_mejor, "mejor"), (c_desastre, "desastre")):
        with col:
            st.subheader(CATEGORIAS[cat])
            top = db.ranking_semanal(cat)
            if not top:
                st.info("Aún no hay participantes esta semana.")
                continue
            st.dataframe(
                [{"#": i + 1, "Usuario": f"@{d['username']}", "Escena": f"{d['obra']} — {d['titulo']}",
                  "Variante": d["variante"], "Votos": d["votos"]} for i, d in enumerate(top)],
                hide_index=True, width="stretch")
            st.markdown("**🥇 El ganador de la semana (por ahora):**")
            ui.tarjeta_doblaje(top[0], user, mis_votos, prefijo=f"rk{cat}")
