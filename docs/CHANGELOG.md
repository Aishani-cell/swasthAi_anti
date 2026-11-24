# Changelog

## 2026-11-06 — Lightweight local RespLLM

- Replaced the NumPy stub that only added a bias to pooled mel bands. Respiratory inference and training now use RespLLM: a CNN–BiGRU encoder, a 768-d embedding, a 4-class head, and a closed-vocabulary GRU decoder.
- Added an ICBHI 2017 reader with cycle extraction, patient-disjoint splits, inverse-frequency class weights, checkpoint resume, and accuracy / precision / recall / F1 / sensitivity / specificity / confusion matrix. Official files are not bundled. A missing dataset returns `DATASET_MISSING` and does not write accuracy.
- Recorded this machine as an i5-14450HX, 24 GB RAM, RTX 3050 6 GB, driver 591.91. Installed PyTorch 2.15.0+cpu because that is the CPython 3.14 wheel. The runtime uses CUDA when `torch.cuda.is_available()` is true and otherwise stays on CPU.
- Stopped the diagnosis path from accepting an LLM primary diagnosis or LLM-written evidence. A local 1.5B model may only agree with the deterministic diagnosis. Drug classes still come from the contraindication table.
- Stopped treating pasted radiology text as model-verified. Qwen3-VL-32B is not loaded.
- Clinical evaluation now records a vision result of `NOT_EVALUATED` when no labeled images exist, and writes the safety confusion matrix from the real vignette run.
