# SwasthAI — Hardware Profile & Resource Adaptation Plan

## 1. Measured System Hardware Specifications

| Component | Measured Specification | Source / Tool |
|---|---|---|
| **Operating System** | Windows 11 (64-bit, Build 26100) | `Win32_OperatingSystem` |
| **Processor (CPU)** | Intel(R) Core(TM) i5-14450HX (10 physical cores: 6 P-cores + 4 E-cores, 16 logical threads) | `Win32_Processor` |
| **Installed System RAM** | 24 GB DDR5 (24,788,948 KB visible, ~14.0 GB free physical RAM) | `Win32_OperatingSystem` |
| **Dedicated GPU** | NVIDIA GeForce RTX 3050 Laptop GPU | `nvidia-smi` |
| **GPU Dedicated VRAM** | 6144 MiB (6.0 GB GDDR6) | `nvidia-smi` |
| **NVIDIA Driver Version** | 591.91 | `nvidia-smi` |
| **Maximum CUDA Version Supported by Driver** | CUDA 13.1 | `nvidia-smi` |
| **Available Storage** | Drive C: ~382 GB free out of 475 GB | `Get-PSDrive` |
| **Python Runtime** | Python 3.14.7 64-bit | `python --version` |
| **PyTorch** | 2.15.0+cpu. `torch.cuda.is_available()` is false. `nvcc` is not on PATH. | `import torch` |
| **Git Tooling** | Git version 2.55.0.windows.3 installed; GitHub CLI (`gh`) not installed | `git --version`, `where gh` |

---

## 2. Resource Constraints & Hardware Bottleneck Analysis

### 2.1 GPU VRAM Capacity (6 GB)
The paper originally cites running large models on two desktop GPUs with 11 GB VRAM each (total 22 GB VRAM):
- `Qwen2.5:14B` for symptom fallback, diagnosis agent, drug-class recommendation agent.
- `Qwen3-VL:32B-Instruct` for radiology vision agent.
- `OPERA-CT` (768-dim audio foundation model) for respiratory acoustics.
- `Qwen2.5:7B` for lab identity suggestions.

**Reality on RTX 3050 Laptop (6 GB VRAM):**
- A 14B parameter model in FP16 requires ~28 GB VRAM; even quantized to 4-bit (GGUF Q4_K_M) it requires ~8.5–9.2 GB VRAM with context, exceeding 6 GB VRAM and inducing heavy paging / system freeze.
- A 32B VLM cannot be loaded in 6 GB VRAM under any practical quantization.
- Running multiple models concurrently is completely impossible on 6 GB VRAM.

### 2.2 Network Bandwidth & Offline Environment
- Current network bandwidth for downloading packages is constrained (~10–20 kB/s with sporadic connection resets).
- Multi-gigabyte model weights (e.g. 14B weights are 9–10 GB each) cannot be automatically fetched without hanging execution.
- The healthpod target deployment environment (e.g. Satnavari village) explicitly requires **offline-capable operation**.

---

## 3. Practical Hardware Adaptation Strategy

In strict adherence to the project prompt guidelines:
1. **Single-Model Sequential Execution:** Never load vision, audio, diagnosis, and drug models simultaneously. Memory management ensures explicitly triggered unloading and garbage collection between stages.
2. **Deterministic-First Paradigm:**
   - **Symptom NLP:** Primary pipeline uses exact bilingual lexicon matching + Ratcliff-Obershelp fuzzy matching (0.90 threshold) + local negation detection (20-char lookahead). This operates deterministically with 0 MB VRAM and sub-millisecond latency.
   - **Safety Engine & Emergency Circuit Breaker:** 100% deterministic rule engine executing without LLM or GPU dependencies.
   - **Laboratory Resolution:** Exact & fuzzy LOINC mapping, unit conversion, and physiological plausibility bounds table.
3. **Reasoning & Agent Models:**
   - Modular model adapter supporting local quantized instruct models (1B–3B class, e.g., Qwen2.5-1.5B/3B, Llama-3.2-1B/3B, or mock/deterministic fallback when models are unconfigured/offline).
   - Reusable inference runtime (reusing the same single active instance for diagnosis and drug recommendations sequentially).
4. **Respiratory Acoustic AI:**
   - Compact Convolutional Recurrent Neural Network (CRNN) & Log-Mel Spectrogram feature extractor with NumPy/PyTorch backend.
   - Optimized for small batch sizes (4–16) with lightweight memory footprint (<50 MB weights).
   - Clean export and fast inference (<100 ms per respiratory cycle).
5. **RAG Knowledge Base:**
   - Layout-aware chunking and cosine similarity index with source/page attribution.
   - Lightweight local embedding vector store with fallback to high-efficiency TF-IDF/BM25/MiniLM embeddings.

---

## 4. Workload Benchmark & Target Latencies

| Pipeline Stage | Target Latency | Target RAM | Target VRAM |
|---|---|---|---|
| Patient Reg / Auth | < 10 ms | < 50 MB | 0 MB |
| Symptom Lexicon & Fuzzy Match | < 20 ms | < 50 MB | 0 MB |
| Lab Extraction & LOINC Resolution | < 50 ms | < 80 MB | 0 MB |
| Deterministic Safety Circuit Breaker | < 5 ms | < 20 MB | 0 MB |
| EvidenceGraph Synthesis | < 15 ms | < 30 MB | 0 MB |
| Local RAG Search (Top-3) | < 80 ms | < 150 MB | 0 MB |
| ML Respiratory Inference | < 120 ms | < 100 MB | < 300 MB (if GPU) |
| Diagnosis & Drug Recommendation | 1.0 – 3.0 s | < 500 MB | < 2.5 GB (if 1.5B-3B active) |
| Report Generation (PDF/JSON) | < 200 ms | < 80 MB | 0 MB |
