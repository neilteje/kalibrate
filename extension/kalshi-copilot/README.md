# Kalshi Copilot Extension

Local-only Chrome extension for `https://demo.kalshi.co/*`.

It overlays a small panel, detects visible market cards, and requests forecasts
from your local bridge API (`python3 -m kalshi.copilot_server`).

## Load

1. Open `chrome://extensions`.
2. Enable **Developer mode**.
3. Click **Load unpacked** and select this folder.

## Notes

- The extension never sends data to remote services directly.
- All model calls happen via your local Python process.
- Default local API URL is `http://127.0.0.1:8765/forecast`.
