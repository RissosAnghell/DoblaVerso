"""Componentes de interfaz compartidos por todas las páginas."""
import base64
from html import escape as esc
import io
import os
import wave
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components

from core import db
from core.config import AUDIO_DIR, CATEGORIAS, PLANES

CSS = """
<style>
.dv-hero {background: linear-gradient(120deg,#FF6A1A 0%,#E8461E 55%,#C7321A 100%);
  color:#fff; padding:2.2rem 2rem; border-radius:18px; margin-bottom:1.2rem;}
.dv-hero h1 {color:#fff; margin:0; font-size:2.6rem;}
.dv-hero p {color:#FFE9DD; margin:.4rem 0 0 0; font-size:1.1rem;}
.dv-kicker {letter-spacing:.2em; font-size:.75rem; font-weight:700; color:#FFD9C4;}
.dv-card {background:#FFFFFF; border:1px solid #F6CDB8; border-radius:14px; padding:1rem 1.1rem; height:100%;}
.dv-card h4 {margin:0 0 .3rem 0; color:#8B1A1A;}
.dv-dark {background:#8B1A1A; color:#FFF1EA; border-radius:14px; padding:1rem 1.1rem;}
.dv-dark h4 {color:#fff; margin:0 0 .3rem 0;}
.dv-banda {background:#8B1A1A; color:#FFF1EA; border-radius:10px; padding:.7rem 1rem; margin:.8rem 0;}
.dv-banda b {letter-spacing:.08em;}
.dv-badge {display:inline-block; background:#FDE3D3; color:#8B1A1A; border-radius:999px;
  padding:.1rem .6rem; font-size:.78rem; font-weight:600; margin-right:.3rem;}
.dv-badge.rojo {background:#8B1A1A; color:#fff;}
</style>
"""


def configurar_pagina(titulo: str, icono: str = "🎙️") -> dict | None:
    """Llamar al inicio de cada página. Devuelve el usuario conectado (o None)."""
    st.set_page_config(page_title=f"{titulo} · DoblaVerso", page_icon=icono, layout="wide")
    db.inicializar()
    st.markdown(CSS, unsafe_allow_html=True)
    return _barra_lateral()


def _barra_lateral() -> dict | None:
    with st.sidebar:
        st.markdown("### 🎙️ DoblaVerso")
        st.caption("Ver, doblar y competir.")
        uid = st.session_state.get("uid")
        user = db.usuario(uid) if uid else None
        if user:
            st.markdown(f"**@{esc(user['username'])}** {insignia_html(user['plan'])}", unsafe_allow_html=True)
            st.caption(f"Plan {user['plan']}")
            if user["suspendido"]:
                st.error("Tu cuenta está suspendida.")
            if st.button("Cerrar sesión", width="stretch"):
                st.session_state.pop("uid", None)
                st.rerun()
        else:
            with st.form("login"):
                nombre = st.text_input("Nombre de usuario", placeholder="ej: benja")
                if st.form_submit_button("Entrar", width="stretch") and nombre.strip():
                    st.session_state["uid"] = db.obtener_o_crear_usuario(nombre)["id"]
                    st.rerun()
            st.caption("Demo: entrar con un nombre crea la cuenta (sin contraseña).")
        return user


def requiere_usuario(user: dict | None) -> dict:
    if not user:
        st.info("👈 Entra con un nombre de usuario en la barra lateral para continuar.")
        st.stop()
    if user["suspendido"]:
        st.error("Tu cuenta está suspendida por moderación.")
        st.stop()
    return user


def admins() -> set[str]:
    lista = os.environ.get("DOBLAVERSO_ADMINS", "")
    try:
        lista = st.secrets.get("admins", lista)
    except Exception:
        pass
    if isinstance(lista, str):
        lista = lista.split(",")
    return {a.strip().lower() for a in lista if a.strip()} or {"admin"}


def es_admin(user: dict | None) -> bool:
    return bool(user) and user["username"] in admins()


def insignia_html(plan: str) -> str:
    texto = PLANES.get(plan, {}).get("insignia")
    if not texto:
        return ""
    clase = "dv-badge rojo" if plan == "Artista" else "dv-badge"
    return f'<span class="{clase}">{texto}</span>'


def banda(etiqueta: str, texto: str) -> None:
    st.markdown(f'<div class="dv-banda"><b>{etiqueta}</b>&nbsp;&nbsp; {texto}</div>', unsafe_allow_html=True)


def tarjeta(titulo: str, texto: str, oscura: bool = False) -> None:
    clase = "dv-dark" if oscura else "dv-card"
    st.markdown(f'<div class="{clase}"><h4>{titulo}</h4>{texto}</div>', unsafe_allow_html=True)


# ------------------------------------------------------------------ audio
def duracion_audio(datos: bytes, nombre: str = "") -> float | None:
    """Duración en segundos. WAV con la librería estándar; otros formatos con mutagen."""
    try:
        with wave.open(io.BytesIO(datos)) as w:
            return w.getnframes() / float(w.getframerate())
    except Exception:
        pass
    try:
        import mutagen
        f = mutagen.File(io.BytesIO(datos))
        return float(f.info.length) if f else None
    except Exception:
        return None


def segundos_de_espera(user: dict) -> int:
    espera = PLANES[user["plan"]]["espera_seg"]
    ultimo = db.ultimo_doblaje_de(user["id"])
    if not espera or not ultimo:
        return 0
    return max(0, int(espera - (datetime.now() - ultimo).total_seconds()))


def fmt_tiempo(s: int) -> str:
    return f"{int(s) // 60}:{int(s) % 60:02d}"


_MIME = {"wav": "audio/wav", "mp3": "audio/mpeg", "ogg": "audio/ogg", "m4a": "audio/mp4", "webm": "audio/webm"}


# ------------------------------------------------------- reproductor sincronizado
def reproductor(video_url: str, inicio: int, fin: int, audio_path: str | None = None,
                audio_inicio: int | None = None, alto: int = 380, clave: str = "") -> None:
    """Video silenciado + pista de doblaje sincronizada (modelo 'audio sincronizado').

    El video nunca se modifica: solo se reproduce encima la pista de la comunidad.
    """
    audio_tag = ""
    if audio_path:
        ruta = AUDIO_DIR / audio_path
        if ruta.exists():
            ext = ruta.suffix.lstrip(".").lower()
            b64 = base64.b64encode(ruta.read_bytes()).decode()
            audio_tag = f'<audio id="a" preload="auto" src="data:{_MIME.get(ext, "audio/wav")};base64,{b64}"></audio>'
    offset = inicio if audio_inicio is None else audio_inicio
    video_url = esc(video_url, quote=True)
    con_pista = "true" if audio_tag else "false"
    html = f"""
<div style="font-family:sans-serif">
  <video id="v" src="{video_url}#t={inicio}" playsinline controls preload="metadata"
     style="width:100%;max-height:{alto - 60}px;border-radius:12px;background:#000"></video>
  {audio_tag}
  <div style="display:flex;gap:1rem;align-items:center;font-size:13px;color:#3A0D0D;margin-top:6px">
    <span>⏱ {fmt_tiempo(inicio)} – {fmt_tiempo(fin)}</span>
    <label style="display:{'inline' if audio_tag else 'none'}">
      <input type="checkbox" id="fondo"> Original de fondo
    </label>
  </div>
</div>
<script>
const v = document.getElementById('v');
const a = document.getElementById('a');
const S = {inicio}, E = {fin}, OFF = {offset}, PISTA = {con_pista};
v.muted = PISTA;
const fondo = document.getElementById('fondo');
if (fondo) fondo.onchange = () => {{ v.muted = !fondo.checked; v.volume = fondo.checked ? 0.15 : 1; }};
v.addEventListener('loadedmetadata', () => {{ if (v.currentTime < S) v.currentTime = S; }});
function sync(forzar) {{
  if (!a) return;
  const t = v.currentTime - OFF;
  if (t < 0 || (a.duration && t > a.duration)) {{ a.pause(); return; }}
  if (forzar || Math.abs(a.currentTime - t) > 0.3) a.currentTime = t;
  if (!v.paused && a.paused) a.play().catch(() => {{}});
}}
v.addEventListener('play', () => {{ if (v.currentTime < S || v.currentTime >= E) v.currentTime = S; sync(true); }});
v.addEventListener('pause', () => a && a.pause());
v.addEventListener('seeked', () => sync(true));
v.addEventListener('timeupdate', () => {{
  if (v.currentTime >= E) {{ v.pause(); v.currentTime = S; if (a) a.pause(); return; }}
  sync(false);
}});
</script>
<!-- {clave} -->
"""
    if hasattr(st, "iframe"):          # Streamlit recientes
        st.iframe(html, height=alto)
    else:                              # versiones anteriores
        components.html(html, height=alto)


# ------------------------------------------------------------- tarjeta de doblaje
def tarjeta_doblaje(d: dict, user: dict | None, mis_votos: set[int], permitir_voto: bool = True,
                    prefijo: str = "") -> None:
    with st.container(border=True):
        cab, cifra = st.columns([4, 1])
        with cab:
            cat = CATEGORIAS.get(d["categoria"], "🎬 Estudio")
            st.markdown(f"**{d['obra']} — {d['titulo']}**  \n"
                        f"@{esc(d['username'])} {insignia_html(d['plan_autor'])} · {cat} · {d['variante'] or ''}",
                        unsafe_allow_html=True)
        cifra.metric("Votos", d["votos"])
        reproductor(d["video_url"], d["inicio"], d["fin"], d["audio_path"], alto=330, clave=f"{prefijo}{d['id']}")
        if not (permitir_voto and user):
            return
        c1, c2 = st.columns(2)
        propio = d["usuario_id"] == user["id"]
        if propio:
            c1.caption("Es tu doblaje 🙂")
        elif d["id"] in mis_votos:
            if c1.button("✓ Votado (quitar)", key=f"{prefijo}q{d['id']}", width="stretch"):
                db.quitar_voto(user["id"], d["id"])
                st.rerun()
        elif c1.button("👍 Votar", key=f"{prefijo}v{d['id']}", type="primary", width="stretch"):
            db.votar(user["id"], d["id"])
            st.rerun()
        with c2.popover("🚩 Reportar", width="stretch"):
            motivo = st.selectbox("Motivo", ["Contenido ofensivo", "Voz suplantada", "Derechos de autor",
                                             "Spam / bots", "Otro"], key=f"{prefijo}m{d['id']}")
            if st.button("Enviar reporte", key=f"{prefijo}r{d['id']}"):
                db.reportar(d["id"], user["id"], motivo)
                st.success("Gracias, el equipo de moderación lo revisará.")
