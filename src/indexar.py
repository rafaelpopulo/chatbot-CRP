"""
Passo 8 — Gera os embeddings (BGE-M3 via Ollama) e indexa os chunks no ChromaDB.

Cria duas coleções na pasta db/:
  - crp_artigos -> 1 chunk por artigo
  - crp_fixos   -> chunks de tamanho fixo

Uso (a partir da raiz do projeto): python src/indexar.py
"""
import json
import time
from pathlib import Path

import chromadb
import ollama

PASTA_DB = "db"
MODELO_EMB = "bge-m3"
LOTE = 16  # quantos textos se enviam ao Ollama de cada vez

COLECOES = {
    "crp_artigos": Path("data/processed/artigos.json"),
    "crp_fixos": Path("data/processed/chunks_fixos.json"),
}


def embed(textos):
    """Recebe uma lista de textos e devolve uma lista de vetores (um por texto)."""
    return ollama.embed(model=MODELO_EMB, input=textos)["embeddings"]


def metadados(chunk):
    """Tudo o que não é o id nem o texto vai como metadado (n.º do artigo, epígrafe, Parte...)."""
    return {k: v for k, v in chunk.items() if k not in ("id", "texto")}


def indexar(client, nome, caminho):
    chunks = json.loads(caminho.read_text(encoding="utf-8"))

    # Apaga a coleção se já existir, para poder correr o script várias vezes sem duplicar dados
    try:
        client.delete_collection(nome)
    except Exception:
        pass
    col = client.create_collection(nome, metadata={"hnsw:space": "cosine"})

    for i in range(0, len(chunks), LOTE):
        lote = chunks[i:i + LOTE]
        col.add(
            ids=[c["id"] for c in lote],
            embeddings=embed([c["texto"] for c in lote]),
            documents=[c["texto"] for c in lote],
            metadatas=[metadados(c) for c in lote],
        )
        print(f"  {nome}: {min(i + LOTE, len(chunks))}/{len(chunks)}", end="\r")
    print(f"  {nome}: {col.count()} chunks indexados          ")


if __name__ == "__main__":
    client = chromadb.PersistentClient(path=PASTA_DB)

    t0 = time.time()
    for nome, caminho in COLECOES.items():
        indexar(client, nome, caminho)
    print(f"Tempo total: {time.time() - t0:.0f} s")

    # Teste rápido: as duas coleções encontram o artigo 24.º?
    pergunta = "A pena de morte é permitida em Portugal?"
    q = embed([pergunta])
    for nome in COLECOES:
        r = client.get_collection(nome).query(query_embeddings=q, n_results=5)
        print(f"\n{nome} — top 5 para: {pergunta}")
        for meta, dist in zip(r["metadatas"][0], r["distances"][0]):
            print(f"  artigos {meta['artigos']:<12} distância {dist:.3f}")