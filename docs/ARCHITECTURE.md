# BIMBA — Arquitectura Técnica

> Plataforma multimodal de notas médicas que transforma grabaciones de clases, PDFs y presentaciones en notas de estudio estructuradas mediante IA.

---

## 1. Visión General del Stack

| Capa | Tecnología | Justificación |
|------|-----------|---------------|
| Frontend | Next.js 14 (App Router) + TypeScript + Tailwind CSS + shadcn/ui | SSR nativo, sistema de archivos como rutas, componentes accesibles listos para usar |
| Backend API | FastAPI (Python 3.11) + async/await | Alto rendimiento I/O-bound, validación Pydantic, documentación OpenAPI automática |
| Workers | Celery + Redis | Cola de tareas distribuida, reintentos automáticos, monitoreo con Flower |
| Base de datos | PostgreSQL 16 + SQLAlchemy (async) + Alembic | ACID, JSONB para contenido de notas, migraciones versionadas |
| Vector DB | Qdrant | Búsqueda semántica vectorial de alta performance, persistente y escalable |
| Almacenamiento | MinIO (S3-compatible) | Auto-hospedado, API S3 estándar, sin costo de egress en producción local |
| Transcripción | faster-whisper (large-v2) | 4x más rápido que Whisper original, soporte multi-idioma, vocabulario médico |
| OCR | pytesseract + pdfplumber + pdf2image | Extracción nativa PDF (pdfplumber) + OCR de imágenes como fallback |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) | Ligero, rápido, suficiente para enlace semántico audio-imagen |
| LLM | Anthropic Claude (claude-sonnet-4-6) | Razonamiento médico superior, ventana de contexto amplia, salida estructurada |
| Video | FFmpeg (python-ffmpeg) | Estándar de la industria, extracción de audio y frames |
| Contenedores | Docker Compose | Entorno reproducible, fácil despliegue local y en VPS |

---

## 2. Flujo de Datos (Diagrama ASCII)

```
Usuario
  │
  │  POST /documents/upload (video/audio/pdf/imagen/URL)
  ▼
┌─────────────────────────────────────┐
│           FastAPI Backend           │
│  - Valida archivo y metadatos       │
│  - Guarda en MinIO                  │
│  - Crea Document + ProcessingJob    │
│  - Encola tarea Celery              │
└──────────────────┬──────────────────┘
                   │ enqueue
                   ▼
┌─────────────────────────────────────┐
│          Redis (Cola)               │
└──────────────────┬──────────────────┘
                   │ consume
                   ▼
┌─────────────────────────────────────────────────────────────┐
│                    Celery Worker                            │
│                                                             │
│  1. Descargar archivo de MinIO                              │
│                                                             │
│  ┌─────────────────┐    ┌──────────────────────────────┐   │
│  │  VIDEO/AUDIO    │    │  PDF                         │   │
│  │                 │    │                              │   │
│  │ FFmpeg          │    │ pdfplumber → texto nativo    │   │
│  │ → audio .wav    │    │ pdf2image → imágenes         │   │
│  │ → frames .jpg   │    │ pytesseract → OCR            │   │
│  │                 │    └──────────────────────────────┘   │
│  │ faster-whisper  │    ┌──────────────────────────────┐   │
│  │ (chunks 5min)   │    │  IMAGEN                      │   │
│  │ → AudioSegments │    │  pytesseract → OCR           │   │
│  │                 │    └──────────────────────────────┘   │
│  │ imagehash       │                                        │
│  │ → VisualFrames  │                                        │
│  │ → OCR frames    │                                        │
│  └────────┬────────┘                                        │
│           │                                                 │
│  2. sentence-transformers                                   │
│     → embeddings de segmentos de audio                      │
│     → embeddings de texto OCR de slides                     │
│     → almacenar en Qdrant                                   │
│                                                             │
│  3. Semantic Linker                                         │
│     → matriz de similitud coseno                            │
│     → SemanticLinks (slide ↔ segmento audio)                │
│                                                             │
│  4. Note Generator (Claude API)                             │
│     → pares (slide + transcripción)                         │
│     → notas estructuradas por sección                       │
│     → guardar Note (JSON) en PostgreSQL                     │
│                                                             │
│  5. Actualizar ProcessingJob → completed                    │
└─────────────────────────────────────────────────────────────┘
                   │
                   │ polling / WebSocket
                   ▼
┌─────────────────────────────────────┐
│           Frontend                  │
│  - Progreso en tiempo real          │
│  - Visor de notas interactivo       │
│  - Export PDF/DOCX/MD/TXT           │
└─────────────────────────────────────┘
```

---

## 3. Estructura de Carpetas

```
BIMBA/
├── docs/
│   └── ARCHITECTURE.md
├── docker-compose.yml
├── .env.example
├── frontend/                          # Next.js 14
│   ├── app/
│   │   ├── (dashboard)/
│   │   │   ├── documents/
│   │   │   └── notes/[id]/
│   │   └── layout.tsx
│   ├── components/
│   │   ├── upload/
│   │   ├── notes/
│   │   └── ui/                        # shadcn/ui
│   └── lib/
│       └── api.ts
└── backend/                           # FastAPI
    ├── Dockerfile
    ├── requirements.txt
    ├── alembic.ini
    ├── alembic/
    │   ├── env.py
    │   └── versions/
    └── app/
        ├── main.py
        ├── config.py
        ├── database.py
        ├── models/
        │   ├── document.py
        │   ├── job.py
        │   ├── segment.py
        │   └── note.py
        ├── schemas/
        │   ├── document.py
        │   ├── job.py
        │   └── note.py
        ├── api/
        │   ├── deps.py
        │   └── v1/
        │       ├── router.py
        │       ├── documents.py
        │       ├── jobs.py
        │       └── notes.py
        ├── services/
        │   ├── storage.py
        │   ├── transcription.py
        │   ├── ocr.py
        │   ├── vision.py
        │   ├── embeddings.py
        │   ├── vector_store.py
        │   ├── semantic_linker.py
        │   └── note_generator.py
        ├── tasks/
        │   ├── celery_app.py
        │   ├── pipeline.py
        │   ├── audio_tasks.py
        │   ├── vision_tasks.py
        │   └── note_tasks.py
        └── utils/
            ├── chunker.py
            ├── ffmpeg.py
            └── exporters.py
```

---

## 4. Modelos de Datos

### Document
```sql
documents (
  id          UUID PRIMARY KEY,
  user_id     UUID,                  -- futuro: auth
  title       TEXT NOT NULL,
  source_type ENUM(video,audio,pdf,image,text,url,youtube),
  source_url  TEXT,                  -- para URLs/YouTube
  file_path   TEXT,                  -- ruta en MinIO
  status      ENUM(pending,processing,completed,failed),
  created_at  TIMESTAMPTZ,
  updated_at  TIMESTAMPTZ
)
```

### ProcessingJob
```sql
processing_jobs (
  id             UUID PRIMARY KEY,
  document_id    UUID FK → documents,
  status         ENUM(pending,processing,completed,failed),
  progress       INTEGER (0-100),
  current_stage  TEXT,               -- "Transcribiendo audio (chunk 3/12)"
  error_message  TEXT,
  started_at     TIMESTAMPTZ,
  completed_at   TIMESTAMPTZ
)
```

### AudioSegment
```sql
audio_segments (
  id           UUID PRIMARY KEY,
  document_id  UUID FK → documents,
  chunk_index  INTEGER,
  start_time   FLOAT,               -- segundos
  end_time     FLOAT,
  transcript   TEXT,
  language     VARCHAR(10)
)
```

### VisualFrame
```sql
visual_frames (
  id           UUID PRIMARY KEY,
  document_id  UUID FK → documents,
  timestamp    FLOAT,               -- segundos (video) o NULL (PDF)
  image_path   TEXT,               -- MinIO path
  slide_number INTEGER,
  ocr_text     TEXT,
  slide_title  TEXT
)
```

### SemanticLink
```sql
semantic_links (
  id                UUID PRIMARY KEY,
  audio_segment_id  UUID FK → audio_segments,
  visual_frame_id   UUID FK → visual_frames,
  similarity_score  FLOAT
)
```

### Note
```sql
notes (
  id              UUID PRIMARY KEY,
  document_id     UUID FK → documents,
  content         JSONB,            -- estructura jerárquica
  format_version  INTEGER DEFAULT 1,
  exported_paths  JSONB             -- {"pdf": "...", "docx": "..."}
)
```

### Estructura JSONB de Note
```json
{
  "title": "Farmacología - Antibióticos Beta-Lactámicos",
  "generated_at": "2024-01-15T10:30:00Z",
  "sections": [
    {
      "id": "sec_1",
      "title": "Mecanismo de Acción",
      "slide_number": 3,
      "timestamp_start": 720.5,
      "timestamp_end": 1020.3,
      "content": "Los antibióticos beta-lactámicos inhiben...",
      "key_concepts": ["transpeptidasa", "PBP", "pared celular"],
      "source_segments": ["seg_uuid_1", "seg_uuid_2"],
      "source_frames": ["frame_uuid_1"]
    }
  ]
}
```

---

## 5. Endpoints de la API

### Documents
| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/v1/documents/upload` | Subir archivo (multipart/form-data) |
| POST | `/api/v1/documents/url` | Procesar URL (YouTube/web) |
| GET | `/api/v1/documents` | Listar documentos |
| GET | `/api/v1/documents/{id}` | Detalle de documento |
| DELETE | `/api/v1/documents/{id}` | Eliminar documento y archivos |

### Jobs
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/v1/jobs/{document_id}` | Estado del procesamiento |
| GET | `/api/v1/jobs/{document_id}/transcript` | Segmentos de transcripción |
| GET | `/api/v1/jobs/{document_id}/frames` | Frames detectados |

### Notes
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/v1/notes/{document_id}` | Notas generadas (JSON) |
| GET | `/api/v1/notes/{document_id}/export/{format}` | Exportar (pdf/docx/md/txt) |
| PATCH | `/api/v1/notes/{document_id}/links` | Corrección manual de enlaces |

---

## 6. Pipeline de Procesamiento

### Estrategia de Chunking

**Audio/Video:**
- Chunks de 5 minutos (300 segundos) con overlap de 10 segundos
- Cada chunk → `AudioSegment` independiente
- Se preservan timestamps absolutos en el documento

**Detección de Cambio de Slide:**
- Extracción de frames a 1fps con FFmpeg
- Hash perceptual (pHash) de cada frame con `imagehash`
- Umbral: diferencia pHash > 10 → nuevo slide
- Reduce frames de ~3600 (1h@1fps) a ~20-50 slides únicos

**Enlace Semántico Audio-Imagen:**
```
Para cada (audio_segment, visual_frame):
  score = cosine_similarity(embed(transcript), embed(ocr_text))
  if score > 0.3:
    crear SemanticLink(audio_segment, visual_frame, score)
```

**Generación de Notas con Claude:**
```
Para cada sección (agrupación por slide):
  contexto = {
    "slide_ocr": frame.ocr_text,
    "slide_title": frame.slide_title,
    "transcripts": [seg.transcript for seg in linked_segments],
    "timestamps": [seg.start_time, seg.end_time]
  }
  → Claude genera nota estructurada SOLO del contenido dado
```

---

## 7. Escalabilidad

### Horizontal
- Workers Celery: escalar réplicas independientemente del backend API
- Backend API: stateless → múltiples instancias detrás de load balancer (Nginx)
- Redis: sentinel o cluster para alta disponibilidad
- PostgreSQL: réplicas de lectura para queries de notas

### Optimizaciones
- Whisper: GPU si disponible (CUDA), fallback CPU automático
- Embeddings: batch processing de segmentos
- Qdrant: índice HNSW para búsqueda aproximada O(log n)
- MinIO: pre-signed URLs para descarga directa sin pasar por backend

### Colas Separadas por Prioridad
```
high_priority:   upload + inicio de pipeline
transcription:   workers con más RAM (Whisper)
ocr:             workers CPU-intensivos
llm:             workers con rate-limiting API
export:          workers livianos
```

---

## 8. Costos Estimados (Servidor VPS Básico)

| Servicio | Costo | Notas |
|----------|-------|-------|
| PostgreSQL + Redis + Qdrant + MinIO | $0 | Auto-hospedado |
| faster-whisper (CPU) | $0 | Local, ~15min por hora de audio |
| Claude API (claude-sonnet-4-6) | ~$0.015/clase | ~1000 tokens input + 2000 output |
| sentence-transformers | $0 | Local |
| VPS (4 CPU, 8GB RAM) | ~$30/mes | Hetzner/DigitalOcean |
| **Total por clase procesada** | ~$0.02 | |
| **100 clases/mes** | ~$32/mes | |

---

## 9. Riesgos Técnicos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|-----------|
| Whisper lento en CPU para videos largos | Alta | Medio | Procesamiento asíncrono, notificación por email/polling |
| Calidad baja de OCR en slides con fórmulas | Media | Alto | Fallback: enviar imagen a Claude Vision |
| Rate limiting Claude API | Baja | Medio | Exponential backoff, cola separada con semáforo |
| MinIO storage lleno | Baja | Alto | Alertas en 80% capacidad, limpieza de archivos temporales |
| Transcripción imprecisa en español médico | Media | Medio | `initial_prompt` con vocabulario médico, modelo large-v2 |

---

## 10. Plan de Implementación

### Fase 1 — Infraestructura (Semana 1)
- [x] docker-compose.yml con todos los servicios
- [x] Modelos SQLAlchemy + migraciones Alembic
- [x] Configuración MinIO + Qdrant
- [ ] Endpoints básicos de upload y listado

### Fase 2 — Pipeline de Procesamiento (Semana 2-3)
- [ ] Integración FFmpeg + extracción de frames
- [ ] Transcripción con faster-whisper chunked
- [ ] OCR con pytesseract + pdfplumber
- [ ] Detección de cambios de slide con imagehash
- [ ] Tareas Celery orquestadas

### Fase 3 — IA y Semántica (Semana 4)
- [ ] Embeddings con sentence-transformers
- [ ] Almacenamiento y búsqueda en Qdrant
- [ ] Semantic linker audio-imagen
- [ ] Generación de notas con Claude API

### Fase 4 — Frontend (Semana 5-6)
- [ ] Dashboard de documentos
- [ ] Visualizador de notas con timeline
- [ ] Export PDF/DOCX/MD
- [ ] Corrección manual de enlaces

### Fase 5 — Producción (Semana 7)
- [ ] Autenticación (NextAuth.js + JWT)
- [ ] Tests de integración
- [ ] Despliegue en VPS con Nginx + SSL
- [ ] Monitoreo (Grafana + Prometheus)
