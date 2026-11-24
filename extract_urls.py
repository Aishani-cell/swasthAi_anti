import re, sys
path = sys.argv[1]
data = open(path, encoding='utf-8', errors='ignore').read()
urls = sorted(set(re.findall(r'https?://[^\"\'\\\s)]+|/[-A-Za-z0-9_./]+\.js', data)))
for u in urls[:80]:
    print(u)
print('TOTAL', len(urls))
