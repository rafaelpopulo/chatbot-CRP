"""
Passos 10 a 13 — Pipeline RAG: recuperação, prompt, geração e interface de linha de comandos.

Uso (a partir da raiz do projeto):
  python src/rag.py              -> conversa com RAG (coleção por artigo)
  python src/rag.py --fixos      -> conversa com RAG (coleção de tamanho fixo)
  python src/rag.py --sem-rag    -> baseline: o LLM responde sem contexto
"""
import sys
import time

import chromadb
import ollama

PASTA_DB = "db"
MODELO_EMB = "bge-m3"
MODELO_LLM = "llama3.1:8b"
K = 5

SISTEMA_RAG = """És um assistente de apoio ao estudo da Constituição da República Portuguesa (CRP).
Regras:
1. Responde APENAS com base nos excertos da CRP que te são fornecidos.
2. Indica sempre os artigos em que te baseias, no formato (art. N.º, n.º X).
3. Se os excertos não tiverem a resposta, diz: "Não encontro resposta a essa pergunta na Constituição." Não inventes.
4. Responde em português de Portugal, de forma clara e concisa.
5. Não dês aconselhamento jurídico sobre casos concretos."""

SISTEMA_BASELINE = """És um assistente de apoio ao estudo da Constituição da República Portuguesa (CRP).
Responde em português de Portugal, de forma clara e concisa, e indica os artigos da CRP em que te baseias."""

_client = chromadb.PersistentClient(path=PASTA_DB)


def embed(texto):
    return ollama.embed(model=MODELO_EMB, input=[texto])["embeddings"]


def recuperar(pergunta, colecao="crp_artigos", k=K):
    """Passo 10: devolve os k chunks mais semelhantes à pergunta."""
    r = _client.get_collection(colecao).query(query_embeddings=embed(pergunta), n_results=k)
    resultados = []
    for texto, meta, dist in zip(r["documents"][0], r["metadatas"][0], r["distances"][0]):
        resultados.append({"texto": texto, "artigos": meta["artigos"], "distancia": dist})
    return resultados


def construir_prompt(pergunta, chunks):
    """Passo 11: junta os excertos recuperados e a pergunta numa só mensagem."""
    blocos = [f"--- Excerto {i} (artigos {c['artigos']}) ---\n{c['texto']}"
              for i, c in enumerate(chunks, start=1)]
    contexto = "\n\n".join(blocos)
    return f"Excertos da CRP:\n\n{contexto}\n\nPergunta: {pergunta}"


def gerar(sistema, mensagem, stream=False):
    """Passo 12: envia o prompt ao Llama 3.1 8B via Ollama e devolve a resposta."""
    mensagens = [{"role": "system", "content": sistema},
                 {"role": "user", "content": mensagem}]
    opcoes = {"temperature": 0.1}

    if not stream:
        return ollama.chat(model=MODELO_LLM, messages=mensagens, options=opcoes)["message"]["content"]

    texto = ""
    for parte in ollama.chat(model=MODELO_LLM, messages=mensagens, options=opcoes, stream=True):
        pedaco = parte["message"]["content"]
        print(pedaco, end="", flush=True)
        texto += pedaco
    print()
    return texto


def responder(pergunta, colecao="crp_artigos", k=K, usar_rag=True, stream=False):
    """Pipeline completo. Devolve (resposta, chunks usados). Na baseline não há chunks."""
    if not usar_rag:
        return gerar(SISTEMA_BASELINE, pergunta, stream), []
    chunks = recuperar(pergunta, colecao, k)
    return gerar(SISTEMA_RAG, construir_prompt(pergunta, chunks), stream), chunks


if __name__ == "__main__":  # Passo 13: interface de linha de comandos
    colecao = "crp_fixos" if "--fixos" in sys.argv else "crp_artigos"
    usar_rag = "--sem-rag" not in sys.argv
    modo = f"RAG ({colecao})" if usar_rag else "sem RAG (baseline)"
    print(f"Chatbot da CRP — modo: {modo}. Escreve 'sair' para terminar.\n")

    while True:
        pergunta = input("Pergunta: ").strip()
        if pergunta.lower() in ("sair", "exit", "q"):
            break
        if not pergunta:
            continue
        t0 = time.time()
        print("\nResposta: ", end="")
        _, chunks = responder(pergunta, colecao, usar_rag=usar_rag, stream=True)
        if chunks:
            print("Artigos recuperados:",
                  "; ".join(f"{c['artigos']} ({c['distancia']:.2f})" for c in chunks))
        print(f"[{time.time() - t0:.0f} s]\n")