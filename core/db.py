"""Base de datos SQLite de DoblaVerso. Todas las consultas pasan por aquí."""
import sqlite3
import uuid
from datetime import datetime, timedelta

from core.config import AUDIO_DIR, DATA_DIR, DB_PATH, DURACION_RULETA, OBRAS_SEMILLA, UMBRAL_PISTA

ESQUEMA = """
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    nombre TEXT,
    bio TEXT DEFAULT '',
    plan TEXT DEFAULT 'Gratis',
    suspendido INTEGER DEFAULT 0,
    creado TEXT
);
CREATE TABLE IF NOT EXISTS escenas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    obra TEXT NOT NULL,
    titulo TEXT NOT NULL,
    tipo TEXT,
    video_url TEXT NOT NULL,
    inicio INTEGER NOT NULL,
    fin INTEGER NOT NULL,
    licencia TEXT,
    activa INTEGER DEFAULT 1
);
CREATE TABLE IF NOT EXISTS doblajes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
    escena_id INTEGER NOT NULL REFERENCES escenas(id),
    modo TEXT NOT NULL,            -- 'ruleta' o 'estudio'
    categoria TEXT,                -- 'mejor' / 'desastre' (solo ruleta)
    variante TEXT,
    inicio INTEGER NOT NULL,       -- segundo del video donde parte el audio
    fin INTEGER NOT NULL,
    audio_path TEXT NOT NULL,
    duracion REAL,
    estado TEXT DEFAULT 'activo',  -- 'activo', 'retirado'
    creado TEXT
);
CREATE TABLE IF NOT EXISTS votos (
    usuario_id INTEGER NOT NULL,
    doblaje_id INTEGER NOT NULL,
    creado TEXT,
    PRIMARY KEY (usuario_id, doblaje_id)
);
CREATE TABLE IF NOT EXISTS reportes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doblaje_id INTEGER NOT NULL,
    usuario_id INTEGER NOT NULL,
    motivo TEXT,
    resuelto INTEGER DEFAULT 0,
    creado TEXT
);
CREATE TABLE IF NOT EXISTS creditos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    obra TEXT NOT NULL,
    idioma TEXT,
    verificado INTEGER DEFAULT 0
);
"""


def ahora() -> str:
    return datetime.now().isoformat(timespec="seconds")


def conectar() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def inicializar() -> None:
    with conectar() as con:
        con.executescript(ESQUEMA)
        if con.execute("SELECT COUNT(*) FROM escenas").fetchone()[0] == 0:
            for obra in OBRAS_SEMILLA:
                for titulo, inicio in obra["escenas"]:
                    con.execute(
                        "INSERT INTO escenas (obra, titulo, tipo, video_url, inicio, fin, licencia) "
                        "VALUES (?,?,?,?,?,?,?)",
                        (obra["obra"], titulo, obra["tipo"], obra["url"], inicio,
                         inicio + DURACION_RULETA, obra["licencia"]),
                    )


# ----------------------------------------------------------------- usuarios
def obtener_o_crear_usuario(username: str) -> dict:
    username = username.strip().lower()
    with conectar() as con:
        fila = con.execute("SELECT * FROM usuarios WHERE username=?", (username,)).fetchone()
        if fila is None:
            con.execute("INSERT INTO usuarios (username, nombre, creado) VALUES (?,?,?)",
                        (username, username.capitalize(), ahora()))
            fila = con.execute("SELECT * FROM usuarios WHERE username=?", (username,)).fetchone()
    return dict(fila)


def usuario(usuario_id: int) -> dict | None:
    with conectar() as con:
        fila = con.execute("SELECT * FROM usuarios WHERE id=?", (usuario_id,)).fetchone()
    return dict(fila) if fila else None


def listar_usuarios() -> list[dict]:
    with conectar() as con:
        return [dict(f) for f in con.execute("SELECT * FROM usuarios ORDER BY username")]


def actualizar_perfil(usuario_id: int, nombre: str, bio: str) -> None:
    with conectar() as con:
        con.execute("UPDATE usuarios SET nombre=?, bio=? WHERE id=?", (nombre, bio, usuario_id))


def cambiar_plan(usuario_id: int, plan: str) -> None:
    with conectar() as con:
        con.execute("UPDATE usuarios SET plan=? WHERE id=?", (plan, usuario_id))


def suspender(usuario_id: int, valor: bool) -> None:
    with conectar() as con:
        con.execute("UPDATE usuarios SET suspendido=? WHERE id=?", (int(valor), usuario_id))


# ------------------------------------------------------------------ escenas
def escenas(solo_activas: bool = True) -> list[dict]:
    sql = "SELECT * FROM escenas" + (" WHERE activa=1" if solo_activas else "") + " ORDER BY obra, inicio"
    with conectar() as con:
        return [dict(f) for f in con.execute(sql)]


def escena(escena_id: int) -> dict | None:
    with conectar() as con:
        fila = con.execute("SELECT * FROM escenas WHERE id=?", (escena_id,)).fetchone()
    return dict(fila) if fila else None


def agregar_escena(obra, titulo, tipo, url, inicio, fin, licencia) -> None:
    if not url.startswith(("https://", "http://")):
        raise ValueError("La URL del video debe empezar con http:// o https://")
    with conectar() as con:
        con.execute(
            "INSERT INTO escenas (obra, titulo, tipo, video_url, inicio, fin, licencia) VALUES (?,?,?,?,?,?,?)",
            (obra, titulo, tipo, url, inicio, fin, licencia))


def activar_escena(escena_id: int, activa: bool) -> None:
    with conectar() as con:
        con.execute("UPDATE escenas SET activa=? WHERE id=?", (int(activa), escena_id))


# ----------------------------------------------------------------- doblajes
def guardar_doblaje(usuario_id, escena_id, modo, categoria, variante, inicio, fin,
                    audio_bytes: bytes, duracion: float, extension: str = "wav") -> int:
    nombre = f"{uuid.uuid4().hex}.{extension}"
    (AUDIO_DIR / nombre).write_bytes(audio_bytes)
    with conectar() as con:
        cur = con.execute(
            "INSERT INTO doblajes (usuario_id, escena_id, modo, categoria, variante, inicio, fin, "
            "audio_path, duracion, creado) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (usuario_id, escena_id, modo, categoria, variante, inicio, fin, nombre, duracion, ahora()))
        return cur.lastrowid


_SELECT_DOBLAJE = """
SELECT d.*, u.username, u.nombre AS autor, u.plan AS plan_autor,
       e.obra, e.titulo, e.tipo, e.video_url, e.licencia,
       (SELECT COUNT(*) FROM votos v WHERE v.doblaje_id = d.id) AS votos
FROM doblajes d
JOIN usuarios u ON u.id = d.usuario_id
JOIN escenas e ON e.id = d.escena_id
"""


def doblajes(where: str = "1=1", params: tuple = (), orden: str = "d.creado DESC", limite: int = 50) -> list[dict]:
    sql = f"{_SELECT_DOBLAJE} WHERE {where} AND u.suspendido=0 ORDER BY {orden} LIMIT {int(limite)}"
    with conectar() as con:
        return [dict(f) for f in con.execute(sql, params)]


def doblaje(doblaje_id: int) -> dict | None:
    with conectar() as con:
        fila = con.execute(_SELECT_DOBLAJE + " WHERE d.id=?", (doblaje_id,)).fetchone()
    return dict(fila) if fila else None


def ultimo_doblaje_de(usuario_id: int) -> datetime | None:
    with conectar() as con:
        fila = con.execute("SELECT MAX(creado) FROM doblajes WHERE usuario_id=?", (usuario_id,)).fetchone()
    return datetime.fromisoformat(fila[0]) if fila and fila[0] else None


def ranking_semanal(categoria: str, limite: int = 10) -> list[dict]:
    desde = (datetime.now() - timedelta(days=7)).isoformat(timespec="seconds")
    return doblajes("d.modo='ruleta' AND d.estado='activo' AND d.categoria=? AND d.creado>=?",
                    (categoria, desde), orden="votos DESC, d.creado ASC", limite=limite)


def pistas_de_obra(obra: str) -> list[dict]:
    """Pistas de comunidad: doblajes activos con suficientes votos (diapositiva 7)."""
    return [d for d in doblajes("e.obra=? AND d.estado='activo'", (obra,),
                                orden="votos DESC", limite=200)
            if d["votos"] >= UMBRAL_PISTA]


def obras() -> list[dict]:
    """Una fila por obra activa, con su video y licencia."""
    with conectar() as con:
        return [dict(f) for f in con.execute(
            "SELECT obra, tipo, video_url, licencia, MIN(id) AS escena_id, COUNT(*) AS n_escenas "
            "FROM escenas WHERE activa=1 GROUP BY obra ORDER BY obra")]


def cambiar_estado_doblaje(doblaje_id: int, estado: str) -> None:
    with conectar() as con:
        con.execute("UPDATE doblajes SET estado=? WHERE id=?", (estado, doblaje_id))


# -------------------------------------------------------------------- votos
def votar(usuario_id: int, doblaje_id: int) -> bool:
    with conectar() as con:
        try:
            con.execute("INSERT INTO votos VALUES (?,?,?)", (usuario_id, doblaje_id, ahora()))
            return True
        except sqlite3.IntegrityError:
            return False


def quitar_voto(usuario_id: int, doblaje_id: int) -> None:
    with conectar() as con:
        con.execute("DELETE FROM votos WHERE usuario_id=? AND doblaje_id=?", (usuario_id, doblaje_id))


def votos_de(usuario_id: int) -> set[int]:
    with conectar() as con:
        return {f[0] for f in con.execute("SELECT doblaje_id FROM votos WHERE usuario_id=?", (usuario_id,))}


# ----------------------------------------------------------------- reportes
def reportar(doblaje_id: int, usuario_id: int, motivo: str) -> None:
    with conectar() as con:
        con.execute("INSERT INTO reportes (doblaje_id, usuario_id, motivo, creado) VALUES (?,?,?,?)",
                    (doblaje_id, usuario_id, motivo, ahora()))


def reportes_pendientes() -> list[dict]:
    with conectar() as con:
        return [dict(f) for f in con.execute(
            "SELECT r.*, u.username AS reportado_por FROM reportes r "
            "JOIN usuarios u ON u.id=r.usuario_id WHERE r.resuelto=0 ORDER BY r.creado")]


def resolver_reportes(doblaje_id: int) -> None:
    with conectar() as con:
        con.execute("UPDATE reportes SET resuelto=1 WHERE doblaje_id=?", (doblaje_id,))


# ----------------------------------------------------------------- créditos
def creditos(usuario_id: int) -> list[dict]:
    with conectar() as con:
        return [dict(f) for f in con.execute("SELECT * FROM creditos WHERE usuario_id=?", (usuario_id,))]


def agregar_credito(usuario_id: int, obra: str, idioma: str) -> None:
    with conectar() as con:
        con.execute("INSERT INTO creditos (usuario_id, obra, idioma) VALUES (?,?,?)", (usuario_id, obra, idioma))


def verificar_credito(credito_id: int, valor: bool) -> None:
    with conectar() as con:
        con.execute("UPDATE creditos SET verificado=? WHERE id=?", (int(valor), credito_id))


def creditos_pendientes() -> list[dict]:
    with conectar() as con:
        return [dict(f) for f in con.execute(
            "SELECT c.*, u.username FROM creditos c JOIN usuarios u ON u.id=c.usuario_id WHERE c.verificado=0")]


# -------------------------------------------------------------- estadísticas
def estadisticas() -> dict:
    with conectar() as con:
        q = lambda s: con.execute(s).fetchone()[0]
        return {
            "usuarios": q("SELECT COUNT(*) FROM usuarios"),
            "doblajes": q("SELECT COUNT(*) FROM doblajes WHERE estado='activo'"),
            "votos": q("SELECT COUNT(*) FROM votos"),
            "escenas": q("SELECT COUNT(*) FROM escenas WHERE activa=1"),
        }
