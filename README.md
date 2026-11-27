# Chatbot de apoio ao Direito Constitucional Português

Protótipo de um chatbot que responde a perguntas sobre a **Constituição da República Portuguesa (CRP)** e indica os artigos em que se baseia. Usa **RAG** (*Retrieval-Augmented Generation*): antes de responder, o sistema procura os artigos relevantes da CRP e o modelo de linguagem responde apenas com base neles, o que reduz as alucinações.

- **Unidade curricular:** Inteligência Artificial — Licenciatura em Engenharia Informática, ISLA (2026/2027)
- **Autor:** Rafael Pópulo (a22505044)
- **Docente:** Jorge Duque
- **Estado:** 2.ª fase intermédia — protótipo inicial

## Arquitetura

![Arquitetura]

1. **Indexação** (corre uma vez): PDF da CRP → texto limpo → divisão em chunks → embeddings → ChromaDB.
2. **Consulta** (em cada pergunta): pergunta → embedding → 5 excertos mais próximos → prompt → LLM → resposta com os artigos citados.

## Tecnologias

| Componente | Escolha |
|---|---|
| Linguagem | Python 3.12 (código próprio, sem LangChain) |
| Extração do PDF | pypdf |
| Embeddings | BGE-M3 (via Ollama, 1024 dimensões) |
| Base vetorial | ChromaDB (distância cosseno) |
| LLM | Llama 3.1 8B (via Ollama, temperatura 0,1) |

## Requisitos

- Python 3.12
- [Ollama](https://ollama.com) instalado e a correr
- Cerca de 8 GB livres em disco para os modelos; 16 GB de RAM recomendados

## Instalação

```bash
# 1. Modelos
ollama pull bge-m3
ollama pull llama3.1:8b

# 2. Ambiente virtual
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS

# 3. Bibliotecas
python -m pip install -r requirements.txt
```

> **Nota (Windows 11):** se o Controlo Inteligente de Aplicações bloquear o `pip.exe`, usa sempre `python -m pip`.

Para confirmar que está tudo a funcionar: `python teste_ambiente.py`

## Utilização

Todos os comandos correm a partir da raiz do projeto.

```bash
# Preparar os dados (só é preciso uma vez)
python src/extrair.py       # PDF → texto limpo
python src/chunking.py      # texto → chunks por artigo e de tamanho fixo
python src/indexar.py       # chunks → embeddings → ChromaDB

# Conversar com o chatbot
python src/rag.py              # RAG, chunks por artigo
python src/rag.py --fixos      # RAG, chunks de tamanho fixo
python src/rag.py --sem-rag    # baseline: o LLM responde sem contexto

# Avaliar
python testes/avaliar.py --so-recuperacao   # só a recuperação (~1 min)
python testes/avaliar.py                    # recuperação + respostas (~40 min no CPU)
```

## Estrutura do projeto

```
chatbot-crp/
├── data/
│   ├── raw/CPR.pdf            # texto oficial da CRP
│   └── processed/             # ficheiros gerados (texto limpo, chunks)
├── docs/                      # diagrama e documentação
├── src/
│   ├── extrair.py             # extração e limpeza do PDF
│   ├── chunking.py            # divisão por artigo e por tamanho fixo
│   ├── indexar.py             # embeddings e indexação no ChromaDB
│   └── rag.py                 # pipeline RAG e interface de linha de comandos
├── testes/
│   ├── avaliar.py             # avaliação automática (20 perguntas)
│   └── resultados.csv         # resultados da última avaliação
├── requirements.txt
└── teste_ambiente.py
```

## Resultados (2.ª fase)

**Recuperação** (18 perguntas dentro do âmbito):

| | Por artigo | Tamanho fixo |
|---|---|---|
| Hit@5 | 94% | 94% |
| MRR | 0,86 | 0,87 |

**Respostas** (20 perguntas, avaliação manual):

| | Com RAG | Sem RAG |
|---|---|---|
| Respostas corretas | 75% | 5% |
| Citações inventadas | nenhuma | em quase todas |
| Recusa de perguntas fora do âmbito | 2/2 | 0/2 |

## Limitações e trabalho futuro

- A pesquisa só semântica falha algumas correspondências literais (ex.: art. 24.º, "pena de morte").
- O LLM por vezes não usa bem um artigo que foi recuperado.
- O conjunto de teste ainda é pequeno (20 perguntas).
- Próximos passos: pesquisa híbrida (BM25 + vetorial), reranker, ajuste do prompt, avaliação com RAGAS, interface Streamlit.

## Fonte dos dados

Constituição da República Portuguesa, VII Revisão Constitucional (2005), texto oficial publicado pela Assembleia da República.

## Aviso

Ferramenta de apoio ao estudo. **Não constitui aconselhamento jurídico.**
