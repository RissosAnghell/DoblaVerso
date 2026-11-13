"""Carga datos de demostración (usuarios, doblajes con audio sintético y votos).

Uso:  python seed_demo.py
Útil para mostrar el ranking y las pistas de comunidad sin grabar nada antes.
"""
import io
import math
import random
import struct
import wave

from core import db
from core.config import DURACION_RULETA


def tono(segundos: float, freq: float, sr: int = 16000) -> bytes:
    """WAV mono con una melodía simple (reemplázalo por voces reales)."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        frames = bytearray()
        for i in range(int(segundos * sr)):
            t = i / sr
            f = freq * (1 + 0.25 * math.sin(2 * math.pi * 0.5 * t))
            env = 0.5 + 0.5 * math.sin(2 * math.pi * 2 * t)
            frames += struct.pack("<h", int(6000 * env * math.sin(2 * math.pi * f * t)))
        w.writeframes(bytes(frames))
    return buf.getvalue()


def main():
    db.inicializar()
    random.seed(7)
    nombres = ["admin", "benja", "cata", "nico", "javi", "sofi", "vozdeoro"]
    users = {n: db.obtener_o_crear_usuario(n) for n in nombres}
    db.cambiar_plan(users["vozdeoro"]["id"], "Artista")
    db.actualizar_perfil(users["vozdeoro"]["id"], "Voz de Oro", "Actor de voz. Anime y series.")
    db.agregar_credito(users["vozdeoro"]["id"], "[Película de ejemplo]", "Español latino")
    db.cambiar_plan(users["cata"]["id"], "VIP")
    db.cambiar_plan(users["nico"]["id"], "Verificado")

    escenas = db.escenas()
    variantes = ["Español chileno", "Español mexicano", "Español argentino", "Otro / inventado"]
    creados = []
    for n in ["benja", "cata", "nico", "javi", "vozdeoro"]:
        for _ in range(2):
            e = random.choice(escenas)
            cat = random.choice(["mejor", "desastre"])
            audio = tono(DURACION_RULETA - 2, random.choice([220, 330, 440]))
            did = db.guardar_doblaje(users[n]["id"], e["id"], "ruleta", cat, random.choice(variantes),
                                     e["inicio"], e["fin"], audio, DURACION_RULETA - 2)
            creados.append((did, n))
    for did, autor in creados:
        for n in random.sample([x for x in nombres if x != autor], k=random.randint(0, 5)):
            db.votar(users[n]["id"], did)
    print(f"Listo: {len(nombres)} usuarios, {len(creados)} doblajes de demo.")


if __name__ == "__main__":
    main()
