import re
import sys
path = sys.argv[1] if len(sys.argv) > 1 else 'c:/Users/Aishani/Downloads/swasthAi/myaadhaar_app.js'
data = open(path, encoding='utf-8', errors='ignore').read()
colors = sorted(set(re.findall(r'#[0-9A-Fa-f]{3,8}', data)))
print('COLORS:', colors[:100])
for kw in ['createTheme', 'primary', 'secondary', 'palette', 'MuiButton', '004d40', '006064', '00796b', '009688', 'fontFamily', 'Roboto', 'borderRadius', 'theme']:
    idx = data.lower().find(kw.lower())
    if idx != -1:
        s = max(0, idx - 150); e = min(len(data), idx + 250)
        print(f'--- {kw} ---')
        print(data[s:e])
