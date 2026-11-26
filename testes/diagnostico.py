import chromadb, ollama

client = chromadb.PersistentClient(path="db")

def embed(texto):
    return ollama.embed(model="bge-m3", input=[texto])["embeddings"]

perguntas = [
    "A pena de morte é permitida em Portugal?",
    "Em Portugal pode haver pena de morte?",
    "Direito à vida",
]

for pergunta in perguntas:
    q = embed(pergunta)
    for nome in ["crp_artigos", "crp_fixos"]:
        r = client.get_collection(nome).query(query_embeddings=q, n_results=30)
        artigos = [m["artigos"] for m in r["metadatas"][0]]
        pos = next((i + 1 for i, a in enumerate(artigos) if "24" in a.split(",")), None)
        print(f"{nome:12} | {pergunta:42} | art. 24.º na posição {pos}")