# Pokemon Card Tracker API

FastAPI service for searching Pokemon card listings and calculating sold listing stats.

## Run locally

```powershell
.venv\Scripts\python.exe -m pip install -r app\requirements.txt
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000

## Deploy on Render

This repo includes `render.yaml` so you can use Blueprint deploy.

1. Push this repository to GitHub.
2. In Render, click **New +** then **Blueprint**.
3. Select this repository.
4. In the Render environment variables panel, set:
   - `EBAY_CLIENT_ID`
   - `EBAY_CLIENT_SECRET`
   - Optional: `EBAY_MARKETPLACE_ID` (default `EBAY_GB`)
5. Deploy.

After deploy, verify:

- `GET /` returns welcome message
- `GET /status` confirms API credential detection
- `POST /search` returns listing data and stats

## Required eBay variables

Create these environment variables in Render:

- `EBAY_CLIENT_ID`
- `EBAY_CLIENT_SECRET`

Optional:

- `EBAY_MARKETPLACE_ID` (`EBAY_GB`, `EBAY_US`, `EBAY_DE`, etc.)
