# 🎙️ DoblaVerso — MVP en Streamlit

*Ver, doblar y competir: la desastrosa perfección del doblaje hecho por la comunidad.*

Prototipo funcional de la propuesta DoblaVerso (Fase 1 + parte de Fase 2): ruleta de 30 s, grabador en el navegador, votos, ranking semanal, pistas de comunidad, perfiles de artista, planes y panel de moderación.

## Cómo ejecutarlo

```bash
python -m venv .venv
source .venv/bin/activate        # En Windows: .venv\Scripts\activate
pip install -r requirements.txt

python seed_demo.py              # (opcional) usuarios, doblajes y votos de ejemplo
streamlit run app.py
```

Se abre en http://localhost:8501. Para entrar escribe cualquier nombre de usuario en la barra lateral (se crea la cuenta). El usuario **admin** ve la página de Moderación.

## Qué hay en cada página

| Página | Diapositiva | Qué hace |
|---|---|---|
| Inicio (`app.py`) | 1, 3 | Los tres pilares, estadísticas y destacados (artistas primero) |
| Ruleta | 6 | Gira → escena al azar de 30 s → grabas → eliges categoría (Mejor doblaje / Desastre glorioso) → publicas |
| Estudio | 3, 5 | Eliges escena, un minuto o un fragmento a medida y grabas; el límite depende del plan |
| Votar y ranking | 6 | Votar, reportar y ranking semanal por categoría |
| Ver con pistas | 7 | Selector de pista: Original u otras de la comunidad que llegaron a 3 votos |
| Perfil | 9 | Perfil, bio, créditos (plan Artista, con verificación) y escenas destacadas |
| Planes | 8 | Tabla de planes y cambio de plan (pago simulado) |
| Moderación | 12, 14 | Reportes (retirar / mantener / suspender), verificar créditos, catálogo y pausar títulos |

## Cómo funciona el modelo legal (diapositiva 13)

- **No se guarda ni se modifica video.** Solo se guarda el audio del usuario.
- El reproductor (`core/ui.py → reproductor`) silencia el video y reproduce la pista de la comunidad sincronizada con él (Opción A, audio sincronizado).
- El catálogo inicial usa solo películas abiertas de la Blender Foundation con licencia Creative Commons (Opción B). Desde Moderación se pueden agregar escenas, pero exige declarar la licencia.

## Configuración

- **Administradores:** crea `.streamlit/secrets.toml` con `admins = "admin,benja"` o usa la variable de entorno `DOBLAVERSO_ADMINS`.
- **Reglas de negocio** (precios, duración por plan, tiempo de espera, votos para ser pista, catálogo): todo está en `core/config.py`.
- **Reiniciar datos:** borra `data/doblaverso.db` y la carpeta `data/audios/`.

## Estructura

```
doblaverso/
├── app.py                 # Inicio
├── pages/                 # Una página por función
├── core/
│   ├── config.py          # Planes, categorías, catálogo semilla
│   ├── db.py              # SQLite
│   └── ui.py              # Estilos, login, reproductor sincronizado, tarjetas
├── seed_demo.py           # Datos de ejemplo
├── data/                  # Base de datos y audios (se crea solo)
└── .streamlit/config.toml # Tema rojo/naranjo de la propuesta
```

## Limitaciones del prototipo y qué cambiar para producción

- **Login sin contraseña.** Para producción usa `st.login()` (Google/Microsoft vía OIDC) o un proveedor como Auth0, y verifica la cuenta para el plan Verificado (anti-bots).
- **Pagos simulados.** Integrar Webpay, Flow o Mercado Pago y confirmar el pago en el servidor antes de cambiar el plan.
- **Almacenamiento local.** SQLite y audios en disco sirven para la demo; en la nube usa PostgreSQL (Supabase/Neon) y un bucket (S3, Cloudflare R2) para los audios. En Streamlit Community Cloud el disco se borra al reiniciar.
- **Audios largos.** El reproductor incrusta el audio en la página; para doblajes de varios minutos conviene servirlos desde un bucket y comprimirlos (MP3/Opus).
- **Sincronización.** Funciona bien con fragmentos de video directos (.mp4). Para plataformas de terceros (Opción A real) se necesitaría una extensión de navegador o un acuerdo con la plataforma.
