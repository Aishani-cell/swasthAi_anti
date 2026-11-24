# Implementation checklist

- [x] Inspect CPU, RAM, GPU, driver, Python, and the repository
- [x] Read the 12-page SwasthAI paper
- [x] Create git branch `backup/pre-lightweight-respllm` and work on `feature/lightweight-respllm`
- [x] Replace the respiratory stub with RespLLM
- [x] Add the ICBHI loader, patient-disjoint split, class weights, resume, and metrics
- [ ] Train on official ICBHI 2017 — blocked until the registered files are in `data/external/icbhi` (see `docs/ICBHI_SETUP.md`)
- [x] Run a synthetic smoke training only as a pipeline check, labeled `synthetic_protocol_smoke`
- [x] Keep diagnosis and drug outputs on deterministic evidence
- [x] Leave vision quantitative metrics unevaluated rather than invent them
- [x] Execute the test suite: `py -3.14 -m pytest tests -q` → 48 passed (6 Nov 2026)
- [x] Synthetic RespLLM smoke training, 25 epochs, CPU, holdout accuracy 1.00 / macro-F1 1.00 on 20 synthetic cycles. Not an ICBHI result.
- [x] API smoke check: `GET /` and `GET /api/v1/models/status` returned 200 via FastAPI TestClient
