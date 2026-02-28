# Fukuin Project Memory

## Project Overview
Japanese text preprocessing app (MTL) — FastAPI backend + Vue 3 frontend.
- Backend: `api/main.py` (FastAPI), `api/db.py` (SQLite)
- Frontend: `frontend/src/` — Pinia store (`stores/app.ts`), API service (`services/api.ts`)
- Main UI components: `DictionaryEditor.vue`, `Processor.vue`

## Architecture
- SQLite DB at `fukuin.db`; single `dictionaries` table + `dictionary_history` table (added)
- Dictionary content stored as JSON string in `content` TEXT column
- Frontend uses Shadcn/Reka UI + Tailwind CSS 4, lucide-vue-next icons

## Dictionary History Feature (implemented)
- `dictionary_history` table: `id, dictionary_id, version_number, content, created_at`
  - FK to `dictionaries(id) ON DELETE CASCADE`
  - Max 500 entries per dictionary (pruned on insert)
- `save_history_entry(cursor, dict_id, content)` helper in `db.py`
- History saved on: dict creation, content change on update, seed
- Endpoints: `GET /dictionaries/{id}/history`, `GET /dictionaries/{dict_id}/history/{version_id}`
- Frontend: "History" view mode in DictionaryEditor sidebar; `HistoryDiff.vue` shows diff
- Diff highlights: green=added, red=removed, yellow=changed (vs current replacementTable)

## Key File Paths
- `api/db.py` — DB init, `save_history_entry`, `seed_db`
- `api/main.py` — All API routes
- `frontend/src/services/api.ts` — Axios API client + TypeScript interfaces
- `frontend/src/stores/app.ts` — Pinia store
- `frontend/src/components/DictionaryEditor.vue` — Main dictionary UI
- `frontend/src/components/DictionaryEditor/HistoryDiff.vue` — Diff component (new)
- `frontend/src/components/DictionaryEditor/JsonTable.vue` — Table editor
- `frontend/src/components/DictionaryEditor/JsonEditor.vue` — JSON editor
