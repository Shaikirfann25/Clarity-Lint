# Clarity Lint — Imperial Jade Web 2.0

A responsive Next.js frontend inspired by the editorial, multi-workspace experience of the supplied Canonry reference. It preserves the Clarity Lint visual identity and connects to the existing FastAPI bridge.

## Requirements
- Node.js 20.9+ (Node 24 is suitable)
- Existing Clarity Lint FastAPI backend on `http://127.0.0.1:8000`

## Install and run (PowerShell)
```powershell
Set-Location "$env:USERPROFILE\Downloads\clarity_lint\Clarity_Lint_Imperial_Jade\web"
npm install
$env:NEXT_PUBLIC_CLARITY_API_URL = "http://127.0.0.1:8000"
npm run dev
```
Open `http://localhost:3000`.

## Backend endpoints used
- `GET /health`
- `GET /api/status`
- `POST /api/analyze`
- `POST /api/document`
- `GET /api/evaluation/demo`
- `POST /api/evaluate` (multipart CSV)

## Notes
The error explorer uses curated illustrative cases. Demo evaluation data is synthetic. The UI explicitly labels those sources and never represents them as validated performance. A clean rule result does not prove that text is unambiguous.
