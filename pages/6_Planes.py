"""Planes de suscripción (diapositiva 8). El pago está simulado."""
import streamlit as st

from core import db, ui
from core.config import PLANES

user = ui.configurar_pagina("Planes", "💳")

st.title("💳 Planes de suscripción")
st.caption("Precios anuales en pesos chilenos (CLP).")


def si_no(v):
    return "✓" if v else "—"


def duracion(p):
    if p["max_seg"] is None:
        return "Ilimitado"
    return "Hasta 2 min" if p["max_seg"] <= 120 else f"Hasta {p['max_seg'] // 60} min"


filas = {
    "Usuario real (anti-bots)": [si_no(p["verificado"]) for p in PLANES.values()],
    "Duración por doblaje": [duracion(p) for p in PLANES.values()],
    "Tiempo de espera": [f"Sí ({p['espera_seg'] // 60} min)" if p["espera_seg"] else "Sin espera"
                         for p in PLANES.values()],
    "Insignias": [p["insignia"] or "—" for p in PLANES.values()],
    "Portafolio y créditos": ["Completo" if p["portafolio"] else "—" for p in PLANES.values()],
    "Primero en Destacados": [si_no(p["destacado"]) for p in PLANES.values()],
}
encabezados = [f"{n}\n${p['precio']:,.0f}".replace(",", ".") for n, p in PLANES.items()]
st.dataframe(
    [{"Beneficio": k, **dict(zip(encabezados, v))} for k, v in filas.items()],
    hide_index=True, width="stretch",
)

st.subheader("Elige tu plan")
cols = st.columns(len(PLANES))
for col, (nombre, p) in zip(cols, PLANES.items()):
    with col:
        precio = "Gratis" if p["precio"] == 0 else f"${p['precio']:,.0f} / año".replace(",", ".")
        ui.tarjeta(nombre, precio, oscura=nombre == "Artista")
        if not user:
            continue
        if user["plan"] == nombre:
            st.button("Tu plan actual", key=f"p{nombre}", disabled=True, width="stretch")
        elif st.button(f"Cambiar a {nombre}", key=f"p{nombre}", width="stretch",
                       type="primary" if nombre != "Gratis" else "secondary"):
            # TODO producción: integrar pasarela (Webpay, Flow o Mercado Pago) y validar el pago en un webhook.
            db.cambiar_plan(user["id"], nombre)
            st.toast(f"Plan cambiado a {nombre} (pago simulado)", icon="✅")
            st.rerun()

if not user:
    st.info("👈 Entra con tu usuario para cambiar de plan.")
ui.banda("DEMO", "El pago está simulado. VIP «sin restricciones» igual respeta las normas de la comunidad.")
