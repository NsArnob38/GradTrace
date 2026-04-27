# GradeTrace Mobile (Expo)

Local-first mobile app for GradeTrace using the existing Supabase auth, API, and MCP services.

## Features in current build

- Supabase login with persistent session
- Real audit history from backend
- Audit detail view (levels, issues, roadmap)
- Smart planner using MCP tools (`plan_path`, `optimize_graduation_path`, `simulate_changes`)
- Transcript upload from camera, gallery, or file picker (PDF/CSV/image)

## Setup

1. Install dependencies from repo root:

```bash
pnpm install
```

2. Configure env for mobile:

```bash
cp packages/mobile/.env.example packages/mobile/.env
```

Set real values in `packages/mobile/.env`.

3. Start Expo:

```bash
pnpm dev:mobile
```

4. Open on phone:
- Install Expo Go
- Scan the QR code shown in terminal

## Important notes

- `EXPO_PUBLIC_MCP_URL` should be your MCP service base URL, without `/v1/tools`.
- Upload size limit currently enforced in app: 12 MB.
- This app does not use mock data; all flows use live backend calls.
