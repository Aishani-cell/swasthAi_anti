import sys, os, subprocess, shutil, glob

print("=== SYSTEM INFO ===")
print("Python executable:", sys.executable)
print("Python version:", sys.version)

total, used, free = shutil.disk_usage(".")
print(f"Disk D: Total {total/(1024**3):.1f} GB, Free {free/(1024**3):.1f} GB")

print("\n=== VIRTUAL ENVS ===")
for p in sorted(glob.glob(".venv*")):
    py = os.path.join(p, "Scripts", "python.exe")
    if os.path.exists(py):
        res = subprocess.run([py, "--version"], capture_output=True, text=True)
        print(f"{p}: {res.stdout.strip()}")
        # Check key packages
        check_code = "import sys; pkgs=['torch','torchvision','transformers','fastapi','streamlit','pytest','pydantic']; " \
                     "found=[p for p in pkgs if __import__('importlib.util').util.find_spec(p) is not None]; " \
                     "print('  Found:', ', '.join(found))"
        res_pkg = subprocess.run([py, "-c", check_code], capture_output=True, text=True)
        print(res_pkg.stdout.strip())

print("\n=== OLLAMA SEARCH ===")
ollama_paths = [
    r"C:\Users\user\AppData\Local\Programs\Ollama\ollama.exe",
    r"C:\Program Files\Ollama\ollama.exe"
]
for op in ollama_paths:
    print(op, "exists:", os.path.exists(op))

print("\n=== HUGGINGFACE CACHE ===")
hf_cache = os.path.expanduser("~/.cache/huggingface/hub")
print("HF cache path:", hf_cache, "exists:", os.path.exists(hf_cache))
if os.path.exists(hf_cache):
    models = os.listdir(hf_cache)
    print("HF models:", models)

print("\n=== TORCH & CUDA in sys.executable ===")
try:
    import torch
    print("Torch version:", torch.__version__)
    print("CUDA available:", torch.cuda.is_available())
    if torch.cuda.is_available():
        print("Device count:", torch.cuda.device_count())
        for i in range(torch.cuda.device_count()):
            print(f"Device {i}: {torch.cuda.get_device_name(i)}")
except Exception as e:
    print("Torch error:", e)
