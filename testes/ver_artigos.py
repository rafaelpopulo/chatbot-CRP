import json

with open("data/processed/artigos.json", encoding="utf-8") as f:
    artigos = {a["numero"]: a for a in json.load(f)}

for n in [24, 30, 288, 286, 122, 128, 148, 49, 57, 37, 13, 65, 64, 222, 115, 19, 33, 172]:
    print(artigos[n]["texto"][:300], "\n")