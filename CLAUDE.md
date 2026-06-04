# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FluxAvision is a retail foot traffic (customer flow) statistics system integrated with Dahua camera SDKs. Full-stack: **Python FastAPI backend** + **Vue 3 + TypeScript + Vite frontend** (with Ant Design Vue), packaged as a **Windows exe installer** via PyInstaller + Inno Setup. The UI and comments are in Chinese.

## Development Commands

### Frontend (from `frontend-vue/` directory)
```bash
npm install          # Install dependencies
npm run dev          # Vite dev server on port 3000 (proxies /api/* to backend:15678)
npm run build        # Production build (outputs to frontend-vue/dist/)
npm run preview      # Preview production build locally
```

### Backend (from `backend/` directory)
```bash
python -m venv venv && venv\Scripts\activate   # Create + activate venv
pip install -r requirements.txt                  # Install dependencies
python main.py                                   # Start API server on port 15678
```

### Production Build (from `backend/` directory)
```bash
build.bat              # One-click build: frontend + backend + PyInstaller
iscc installer.iss     # Generate Windows installer (requires Inno Setup 6.x)
```

### Activation Code Generation
```bash
cd tools
python generate_activation.py --fingerprint <fingerprint> --channels 4 --days 365
```

**There is no test suite, no CI/CD pipeline, and no Docker configuration.**

## Architecture

### Frontend — Client-Side SPA on Vue 3 + Vite

The frontend lives in `frontend-vue/` (separate from the legacy `src/` which contains the old Next.js code). Everything renders from a single `App.vue` using Vue `ref()` state with a custom `Sidebar` component handling navigation. Each page is a component in `frontend-vue/src/components/`:

- `auth/LoginPage.vue` — License activation + password login
- `dashboard/Dashboard.vue` — Metrics cards + ECharts area/bar charts
- `devices/DeviceManagement.vue` — Device CRUD + collector status + video preview
- `history/HistoryData.vue` — Historical traffic data queries + CSV export
- `large-screen/LargeScreenView.vue` — Full-screen display mode with video grid
- `layout/Header.vue` — Top bar (breadcrumb, store name, clock)
- `layout/Sidebar.vue` — Left sidebar navigation
- `settings/SystemSettings.vue` — Store name, password, dashboard metrics config
- `settings/LargeScreenSettings.vue` — Large screen template/config + license
- `video/RTSPVideoPlayer.vue` — WebSocket + snapshot polling player, Canvas rendering with frame dropping

**Key patterns:**
- No Vue Router — pure `ref()` based page switching (matches original React pattern)
- No Pinia/Vuex — all state is local via `ref()` / `reactive()`
- Direct `fetch()` calls to `/api/*` endpoints — no API client abstraction
- Toast via `vue-sonner`: `import { toast } from 'vue-sonner'`, then `toast.success()` / `toast.error()`
- UI: Ant Design Vue 4 (`a-modal`, `a-table`, `a-select`, `a-tabs`, etc.) + Tailwind CSS v4
- Charts: ECharts via `vue-echarts` with tree-shakable imports
- Icons: `lucide-vue-next` (use `markRaw()` when storing in reactive data)
- Path alias: `@/*` → `./src/*`
- Dark navy theme (`#0a192f`) with cyan accent (`#00d9ff`)

### Backend — FastAPI with SQLite

- **Entry point**: `backend/main.py` — FastAPI app, lifespan events, static file serving
- **Database**: SQLite3 (WAL mode) + SQLAlchemy ORM. Hand-rolled migrations in `database.py`
- **Routers**: Flat files in `backend/routers/`, registered centrally in `routers/__init__.py`. All under `/api/` prefix
- **API response format**: `{ success: boolean, data?: any, message?: string }`

**Key modules:**
- `dahua_collector.py` — Dahua SDK client with exponential backoff reconnection (3s → 30s)
- `stream_manager.py` — OpenCV RTSP-to-MJPEG, one capture thread per camera shared across HTTP clients
- `field_crypto.py` — AES-256-CBC field encryption (passwords, activation codes stored as `ENC:` prefix)
- `license_crypto.py` — Ed25519 signature verification for license activation
- `config.py` — Path resolution, DB config, AES key management, hardware fingerprint
- `windows_service.py` — System tray, auto-start, single-instance enforcement

### Optimized Video Streaming (v2.2.0+)

The video streaming pipeline has been optimized to address customer-reported buffering/latency:

#### Backend (`stream_manager.py`) Optimizations
1. **Resolution Scaling** (`SCALE_WIDTH=640`): Raw RTSP frames (typically 1920×1080) are scaled down before JPEG encoding. This reduces JPEG size by ~80-90% (from 80-150KB to 8-20KB per frame), dramatically cutting bandwidth, network latency, and browser decode overhead.
2. **Frame Rate Control** (`CAPTURE_FPS=15`): The capture thread only encodes frames at the target FPS, skipping intermediate frames. This reduces CPU usage by ~40-60% compared to encoding every camera frame (typically 25fps).
3. **Aggressive Low-Latency FFmpeg** (`AGGRESSIVE_LOW_LATENCY=True`): Additional FFmpeg options (`probesize=32`, `analyzeduration=0`, `max_delay=0`, `reorder_queue_size=0`) further reduce the RTSP internal buffer latency.
4. Config constants are directly in `stream_manager.py` and can be tuned per deployment.

#### Frontend (`RTSPVideoPlayer.vue`) Optimizations
1. **Canvas Rendering**: Replaced `<img>` tag with `<canvas>` element + `createImageBitmap()` for more efficient frame decoding and rendering.
2. **Frame Dropping**: If a frame is still being decoded when a new one arrives, it's silently dropped. Prevents the queue buildup that caused visible stuttering.
3. **No Blob URL Race Conditions**: Eliminated `URL.createObjectURL()` / `URL.revokeObjectURL()` pattern which caused flicker under load.
4. WebSocket remains primary transport; HTTP snapshot polling is the fallback.

#### Transport
- Primary: WebSocket binary JPEG push at ~15fps (`/api/devices/{id}/stream/ws`)
- Fallback: HTTP snapshot polling at 200ms intervals (`/api/devices/{id}/snapshot`)
- Legacy: MJPEG HTTP stream (`/api/devices/{id}/stream`) for compatibility

### Security Architecture (4 layers)
1. Hardware fingerprint binding (CPU + motherboard + disk + MAC → SHA-256)
2. Database key protection (AES-encrypted `.key` file bound to fingerprint)
3. AES-256-CBC field encryption (random IV per encryption)
4. Ed25519 digital signature licensing (public key in client, private key on licensing platform)

## Vite Configuration

- **Dev mode**: `frontend-vue/vite.config.ts` with `server.proxy: { '/api': { target: 'http://127.0.0.1:15678' } }`
- **Production/build mode**: `base: './'` (relative paths for FastAPI serving), outputs to `frontend-vue/dist/`
- `build.bat` copies `frontend-vue/dist/` → `backend/frontend-build/`, then PyInstaller bundles into `static/`

## Environment Variables

Set in `backend/config.py` (with `python-dotenv`):
- `API_HOST` (default: `0.0.0.0`)
- `API_PORT` (default: `15678`)
- `CORS_ORIGINS` (default: `*`)

## Conventions

- TypeScript strictness is relaxed (`noImplicitAny: false`)
- `frontend-vue/` is the active frontend; `src/` contains legacy Next.js code (to be cleaned up)
- ID generation: UUID4 truncated to 25 hex chars (`uuid.uuid4().hex[:25]`)
- Dates stored as UTC via `datetime.utcnow()`; traffic records use `YYYY-MM-DD` date strings + integer hours
- Code identifiers are in English; UI text and comments are in Chinese
- Ant Design Vue components used for structural behavior (modals, tables, selects); Tailwind handles visual styling
- RTSP URL generation utility: `generateRtspUrl()` in `frontend-vue/src/lib/utils.ts`
