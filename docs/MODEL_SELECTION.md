# Model selection for this laptop

Measured on 6 November 2026:

| Item | Measured value |
|---|---|
| CPU | Intel Core i5-14450HX, 10 cores, 16 threads |
| RAM | 24 GB DDR5 (25,383,882,752 bytes) |
| GPU | NVIDIA GeForce RTX 3050 6GB Laptop GPU, 6144 MiB, driver 591.91, compute capability 8.6 |
| CUDA toolkit (`nvcc`) | Not on PATH |
| Python | 3.14.7 |
| PyTorch | 2.15.0+cpu from PyPI (`torch.version.cuda` is `None`, `torch.cuda.is_available()` is false) |

The PyPI wheel for CPython 3.14 is a 127 MB CPU build. A 32B or 14B model is not loaded. The driver can support a newer CUDA runtime, but no CUDA wheel was installed in this pass because the published PyPI artifact for this interpreter is CPU-only. Respiratory training and inference use that CPU build and will move to CUDA automatically if a CUDA build of PyTorch later reports `torch.cuda.is_available()`.

## What replaced the paper's large models

| Paper component | Original model | On this machine |
|---|---|---|
| Radiology | Qwen3-VL-32B-Instruct | Not loaded. Metadata audit plus operator-entered text. No pixel diagnosis is emitted. |
| Symptom fallback, diagnosis, drug reasoning | Qwen2.5-14B via Ollama | Deterministic evidence graph and drug-class table. Optional local `qwen2.5:1.5b-instruct` may only confirm the same primary diagnosis. It cannot write evidence citations or drug classes. |
| Lab identity suggestions | Qwen2.5-7B | Existing LOINC alias resolver. |
| Respiratory embedding | Frozen OPERA-CT, 768-d | RespLLM encoder, trained here, projects to 768-d. OPERA-CT weights are not bundled. |
| RespLLM (paper Section 6) | Named as future work, no layer sizes in the paper | CNN–BiGRU encoder, 4-class ICBHI head, GRU decoder over a fixed clinical token list. About 1–2 million parameters. |

Only one torch module is marked active. Training and inference call `release_torch_memory()` when they finish. A CUDA out-of-memory error retries the respiratory model on CPU.

## RespLLM configuration

- Audio: 16 kHz, 64 mel bins, frames fit to 128
- Encoder: Conv 1→16→32, GroupNorm, ReLU, 2×2 pooling, BiGRU hidden 64
- Embedding: attention pool, linear map to 768, tanh
- Classes: normal, crackle, wheeze, both
- Decoder vocabulary: acoustic descriptors plus “review required” and “not a diagnosis”
- Parameter count measured after construction: 245,287
- Loss: weighted cross-entropy plus 0.35 caption loss
- Optimizer: AdamW, gradient clip 1.0
- Checkpoint: `ml/respiratory/checkpoints/best_respllm.pt`

## Not claimed

- ICBHI 2017 scores, until that dataset is installed and a run finishes
- Paper Table 2 numbers as if they were reproduced with Qwen2.5-14B on two GTX 1080 Ti GPUs
- Vision accuracy
