import re
data = open('c:/Users/Aishani/Downloads/swasthAi/backend/app/agents/symptom_agent/lexicon.py', encoding='utf-8').read()
canonicals = re.findall(r'"canonical": "([^"]+)"', data)
print("CANONICALS (%d):" % len(canonicals))
for c in canonicals:
    print(" -", c)
