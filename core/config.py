"""Configuración central de DoblaVerso (planes, categorías y catálogo semilla)."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
AUDIO_DIR = DATA_DIR / "audios"
DB_PATH = DATA_DIR / "doblaverso.db"

# Duración de una escena de la ruleta (segundos) y margen de tolerancia al grabar
DURACION_RULETA = 30
MARGEN_GRABACION = 5

# Votos que necesita un doblaje del Estudio para aparecer como pista seleccionable
UMBRAL_PISTA = 3

# ---------------------------------------------------------------------------
# Planes (diapositiva 8). Precios anuales en CLP.
#   max_seg = None  -> ilimitado
#   espera_seg      -> tiempo mínimo entre grabaciones (0 = sin espera)
# ---------------------------------------------------------------------------
PLANES = {
    "Gratis": {
        "precio": 0, "max_seg": 120, "espera_seg": 120,
        "verificado": False, "insignia": None, "portafolio": False, "destacado": False,
    },
    "Verificado": {
        "precio": 5000, "max_seg": 600, "espera_seg": 60,
        "verificado": True, "insignia": "✓ Verificado", "portafolio": False, "destacado": False,
    },
    "VIP": {
        "precio": 10000, "max_seg": None, "espera_seg": 0,
        "verificado": True, "insignia": "★ VIP", "portafolio": False, "destacado": False,
    },
    "Artista": {
        "precio": 15000, "max_seg": None, "espera_seg": 0,
        "verificado": True, "insignia": "✓ Verificado · 🎙️ Artista", "portafolio": True, "destacado": True,
    },
}

CATEGORIAS = {
    "mejor": "🏆 Mejor doblaje",
    "desastre": "💥 Desastre más glorioso",
}

VARIANTES = [
    "Español chileno", "Español mexicano", "Español argentino", "Español caribeño",
    "Español neutro", "Español de España", "Inglés", "Otro / inventado",
]

TIPOS = ["Película", "Serie", "Anime", "Corto"]

# ---------------------------------------------------------------------------
# Catálogo semilla: solo contenido con licencia libre (Opción B de la diapositiva 13).
# Películas abiertas de la Blender Foundation, licencia CC BY.
# ---------------------------------------------------------------------------
_GCS = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/"
OBRAS_SEMILLA = [
    {"obra": "Big Buck Bunny", "tipo": "Corto", "url": _GCS + "BigBuckBunny.mp4",
     "licencia": "CC BY 3.0 · Blender Foundation", "escenas": [
        ("El despertar del conejo", 30), ("Las ardillas molestosas", 150),
        ("La mariposa", 250), ("La trampa", 420), ("La venganza", 480)]},
    {"obra": "Elephants Dream", "tipo": "Película", "url": _GCS + "ElephantsDream.mp4",
     "licencia": "CC BY 2.5 · Blender Foundation", "escenas": [
        ("Los cables", 20), ("La máquina", 120), ("Discusión en el puente", 330), ("El final", 560)]},
    {"obra": "Sintel", "tipo": "Película", "url": _GCS + "Sintel.mp4",
     "licencia": "CC BY 3.0 · Blender Foundation", "escenas": [
        ("La nieve", 15), ("El guardián", 115), ("La cueva", 470), ("El dragón", 600)]},
    {"obra": "Tears of Steel", "tipo": "Película", "url": _GCS + "TearsOfSteel.mp4",
     "licencia": "CC BY 3.0 · Blender Foundation", "escenas": [
        ("El puente", 10), ("El reencuentro", 90), ("Los robots", 380), ("Último intento", 560)]},
]
