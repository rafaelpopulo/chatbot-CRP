import pypdf, chromadb, ollama

v = ollama.embed(model="bge-m3", input="Artigo 24.º — Direito à vida")["embeddings"][0]
print("Embedding OK, dimensão:", len(v))   # deve dar 1024

r = ollama.chat(model="llama3.1:8b", messages=[{"role": "user", "content": "Diz olá em português de Portugal."}])
print("LLM OK:", r["message"]["content"])

print("ChromaDB OK, versão:", chromadb.__version__)