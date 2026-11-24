# BILLI R-20 Roadmap

## Deployment foundation
- [x] Root FastAPI entrypoint (main.py)
- [x] Root Python dependencies and Python 3.12 pin
- [x] Static web assets under public/
- [x] Vercel project configuration
- [x] CI workflow for backend tests
- [ ] Verify first Vercel deployment in the user's Vercel account

## Application modules
- [x] Deterministic Nanobot Lite intent router (starter)
- [x] Consent-gated Mem0 Lite SQLite helper (starter)
- [x] CALM / RUGGED visual mode preview
- [x] Expression control preview
- [x] Browser voice capability detection
- [x] ESP32 hardware simulator view
- [ ] Real SQLite/FTS5 RAG knowledge engine
- [ ] Chat-to-memory orchestration with consent
- [ ] Full multilingual response composition
- [ ] Reference-matched 3D robot model and face animation
- [ ] Persistent cloud storage integration
- [ ] Google Drive OAuth and private sync
- [ ] ESP32 export validation and physical firmware integration

## Safety / status rules

A demo intent response is not a full language model. An empty or unconfigured knowledge source must not be represented as connected. Hardware remains simulated until a physical ESP32 is connected and tested. Vercel filesystem data is ephemeral; use a persistent managed database before relying on hosted memory or knowledge writes.