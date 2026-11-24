import re, shutil, subprocess, sys

print("python:", sys.version)
print("dot available:", shutil.which("dot") is not None)

try:
    import psutil
    mem = psutil.virtual_memory()
    print("RAM GB:", round(mem.total / 1e9, 1), " avail GB:", round(mem.available / 1e9, 1))
    print("CPU cores:", psutil.cpu_count())
except Exception as e:
    print("psutil unavailable:", e)
    out = subprocess.run(["powershell", "-Command", "Get-CimInstance Win32_PhysicalMemory | Measure-String -Property Capacity -Sum"], capture_output=True, text=True)
    print(out.stdout[:500])

try:
    import graphviz
    print("graphviz python: OK")
except Exception as e:
    print("graphviz python: NOT available:", e)

data = open('c:/Users/Aishani/Downloads/swasthAi/backend/app/agents/symptom_agent/lexicon.py', encoding='utf-8').read()
print("lexicon has fever:", 'fever' in data, "| bukhar:", 'bukhar' in data, "| chakkar:", 'chakkar' in data, "| saans:", 'saans' in data, "| breathless:", 'breath' in data)
