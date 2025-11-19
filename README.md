# FinTrack – Seguimiento financiero multimoneda

FinTrack es un MVP completo para registrar ingresos y gastos multiusuario con control simultáneo en ARS, USD y BTC. El stack se entrega dockerizado e incluye:

- **Frontend** en Next.js + React + Tailwind para dashboards responsive, carga de movimientos, administración de cuentas y categorías.
- **Backend** en FastAPI + SQLAlchemy + Alembic con autenticación JWT por cookie HttpOnly, scheduler para cotizaciones y tests en pytest.
- **Base de datos** PostgreSQL 15.

El objetivo es simplificar el seguimiento de ingresos (USD), gastos (ARS) y ahorros (BTC) conservando la cotización utilizada en cada registro.

## Arquitectura

```
.
├── backend/        # FastAPI, modelos, CRUD, migraciones, tests
├── frontend/       # App React/Next.js (Tailwind, Chart.js)
├── .envs/          # Templates de variables de entorno (dev/prod)
└── docker-compose.yml
```

### Backend
- CRUD para usuarios, cuentas, categorías/subcategorías y transacciones.
- Conversión automática de montos a ARS/USD/BTC usando la cotización diaria guardada en `exchange_rates`.
- Scheduler (`APScheduler`) que consulta **DolarAPI** y **Coingecko** a diario para almacenar el tipo de cambio.
- Seeds iniciales: monedas base, fuentes de cotización, cuentas y categorías por defecto al crear usuario.
- Tests con pytest cubriendo autenticación, conversiones y scheduler.

### Frontend
- Flujo de registro/login con mantenimiento de sesión vía cookie (FastAPI emite JWT HttpOnly).
- Dashboard responsive: métricas, evolución mensual, top categorías, últimos movimientos.
- Formularios para registrar transacciones, administrar categorías/subcategorías y cuentas.
- UI dark-mode inspirada en apps móviles de finanzas, lista para usarse en desktop o mobile web.

## Configuración

1. Revisá y ajustá los templates de variables de entorno ubicados en `.envs/dev`:
   - `.envs/dev/backend.env`
   - `.envs/dev/frontend.env`
   - `.envs/dev/db.env`

   > Las variantes en `.envs/prod` sirven como guía para despliegues.

   Actualizá los secretos (`JWT_SECRET`, contraseñas, dominio de cookies, etc.) antes de levantar el stack.

2. Levantá los servicios con Docker Compose:
   ```bash
   docker-compose up --build
   ```
   - El backend ejecuta automáticamente `alembic upgrade head` y `python app/initial_data.py` antes de iniciar `uvicorn`.
   - El frontend quedará disponible en http://localhost:3000 y consumirá el backend en http://localhost:8000.

3. Accedé a la app web, registrá un usuario y comenzá a cargar movimientos.

## Desarrollo local sin Docker

1. Backend
   ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements-dev.txt
   export DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/finance
   alembic upgrade head
   python app/initial_data.py
   uvicorn app.main:app --reload
   ```

2. Frontend
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   Ajustá `NEXT_PUBLIC_API_URL` según corresponda.

## Tests

Los tests de backend se encuentran en `backend/tests`:
```bash
cd backend
python3 -m pip install -r requirements-dev.txt
python3 -m pytest
```

Las pruebas cubren:
- Registro/login y persistencia de defaults.
- Creación de transacciones con conversión a múltiples monedas.
- Scheduler de cotizaciones (usando mocks para evitar llamadas reales a APIs externas).

## API externa utilizada

- **DolarAPI** (`https://dolarapi.com/v1/dolares/`): tasas oficial y blue USD/ARS.
- **Coingecko** (`https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd,ars`): cotizaciones BTC/USD y BTC/ARS.

Las respuestas se almacenan en la tabla `exchange_rates` y se referencian desde cada transacción para mantener trazabilidad.

## Próximos pasos sugeridos
- Agregar paginación y filtros más avanzados al listado de transacciones.
- Incorporar presupuestos mensuales y alertas por categoría.
- Añadir soporte para adjuntar comprobantes (archivos) a cada movimiento.

¡Listo! Con este stack podés monitorear tu flujo de dinero en Argentina sin perder de vista el impacto de las cotizaciones.
