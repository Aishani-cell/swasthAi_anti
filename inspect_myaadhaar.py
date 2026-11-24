import re
data = open('c:/Users/Aishani/Downloads/swasthAi/myaadhaar_home.html', encoding='utf-8', errors='ignore').read()
print('SCRIPTS:', re.findall(r'src="([^"]+\.js[^"]*)"', data))
print('CSS:', re.findall(r'href="([^"]+\.css[^"]*)"', data))
print(data[:2000])
