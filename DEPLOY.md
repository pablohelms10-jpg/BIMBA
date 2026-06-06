# DEPLOY EN 10 MINUTOS

Stack: **Railway** (backend + PostgreSQL + Redis + Celery worker) + **Vercel** (frontend Next.js)

Sin MinIO, sin Qdrant, sin servidores propios.

---

## Sección 1 — Railway (Backend)

### 1. Crear el proyecto

1. Ir a [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo**
2. Seleccionar el repo **BIMBA**
3. Railway detecta el `Dockerfile` en `backend/` automáticamente gracias a `railway.toml`

### 2. Agregar PostgreSQL

1. En el proyecto → click **"+ New"** → **"Database"** → **"Add PostgreSQL"**
2. Railway crea la variable `DATABASE_URL` automáticamente y la inyecta en el servicio

### 3. Agregar Redis

1. Click **"+ New"** → **"Database"** → **"Add Redis"**
2. Railway crea `REDIS_URL` automáticamente

### 4. Configurar variables del backend

En el servicio backend → pestaña **Variables** → agregar:

```
ANTHROPIC_API_KEY=sk-ant-...
USE_LOCAL_STORAGE=true
USE_QDRANT=false
SECRET_KEY=cualquier-string-largo-aleatorio-minimo-32-chars
CORS_ORIGINS=https://tu-app.vercel.app
```

> `USE_LOCAL_STORAGE=true` guarda archivos en el disco del contenedor (Railway persiste el volumen).
> `USE_QDRANT=false` usa similitud coseno en memoria — sin servidor externo.

### 5. Agregar el worker Celery

1. Click **"+ New"** → **"Empty Service"** → conectar al **mismo repo BIMBA**
2. En el servicio worker → **Settings** → **Start Command**:
   ```
   celery -A app.tasks.celery_app worker --loglevel=info --concurrency=2
   ```
3. El worker hereda `DATABASE_URL` y `REDIS_URL` del mismo entorno de Railway

### 6. Obtener la URL pública del backend

En el servicio backend → pestaña **Settings** → **Networking** → **Generate Domain**

Copiar la URL, por ejemplo: `https://bimba-backend-production.up.railway.app`

---

## Sección 2 — Vercel (Frontend)

1. Ir a [vercel.com](https://vercel.com) → **New Project** → importar el repo **BIMBA**
2. En **"Root Directory"** escribir: `frontend`
3. En **Environment Variables** agregar:
   ```
   NEXT_PUBLIC_API_URL=https://bimba-backend-production.up.railway.app/api/v1
   ```
   (reemplazar con la URL real de Railway del paso anterior)
4. Click **Deploy**

Vercel detecta Next.js automáticamente con la configuración de `vercel.json`.

---

## Sección 3 — Listo

La URL de tu aplicación es la que Vercel muestra al terminar el deploy, del tipo:
`https://bimba-xxxx.vercel.app`

### Verificar que todo funciona

- Frontend: abrir la URL de Vercel en el navegador
- Backend health: `https://tu-backend.railway.app/health` → debe devolver `{"status":"ok"}`
- Backend docs: `https://tu-backend.railway.app/docs`

---

## Costos estimados (tier gratuito)

| Servicio | Costo |
|----------|-------|
| Railway  | $5/mes — con $5 de crédito inicial gratis el primer mes sale $0 |
| Vercel   | Gratis para proyectos personales |
| **Total mes 1** | **$0** |
| **Total mes 2+** | **~$5/mes** |

> Railway Hobby Plan: $5/mes incluye PostgreSQL, Redis, y el backend. El worker Celery consume recursos adicionales; monitorear en el dashboard de Railway.

---

## Variables de entorno completas (referencia)

### Backend (Railway)

| Variable | Valor |
|----------|-------|
| `ANTHROPIC_API_KEY` | `sk-ant-...` (requerido) |
| `USE_LOCAL_STORAGE` | `true` |
| `USE_QDRANT` | `false` |
| `SECRET_KEY` | string aleatorio largo |
| `CORS_ORIGINS` | URL de Vercel |
| `DATABASE_URL` | inyectado por Railway automáticamente |
| `REDIS_URL` | inyectado por Railway automáticamente |

### Frontend (Vercel)

| Variable | Valor |
|----------|-------|
| `NEXT_PUBLIC_API_URL` | `https://tu-backend.railway.app/api/v1` |
