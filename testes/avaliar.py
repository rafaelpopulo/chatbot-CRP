"""
Passos 16 a 18 — Avaliação automática do protótipo.

Uso (a partir da raiz do projeto):
  python testes/avaliar.py                    -> recuperação + respostas (≈45 min no CPU)
  python testes/avaliar.py --so-recuperacao   -> só a recuperação (≈1 min)

Resultados em testes/resultados.csv (abre no Excel).
"""
import csv
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from rag import recuperar, responder  # noqa: E402

K = 5
SAIDA = Path("testes/resultados.csv")

# (id, pergunta, artigos esperados) — igual ao separador "Testes" da folha
PERGUNTAS = [
    ("P01", "A pena de morte é permitida em Portugal?", [24]),
    ("P02", "Pode haver prisão perpétua em Portugal?", [30]),
    ("P03", "Que matérias não podem ser alteradas numa revisão constitucional?", [288]),
    ("P04", "Uma maioria de 2/3 eleita com um programa monárquico pode restaurar a monarquia?", [288, 286]),
    ("P05", "Que idade é preciso ter para ser candidato a Presidente da República?", [122]),
    ("P06", "Quanto tempo dura o mandato do Presidente da República?", [128]),
    ("P07", "Quantos deputados tem a Assembleia da República?", [148]),
    ("P08", "Com que idade se pode votar?", [49]),
    ("P09", "O direito à greve está protegido na Constituição?", [57]),
    ("P10", "O que diz a Constituição sobre a liberdade de expressão?", [37]),
    ("P11", "Todos os cidadãos são iguais perante a lei?", [13]),
    ("P12", "Existe um direito à habitação?", [65]),
    ("P13", "O Estado tem de garantir um serviço nacional de saúde?", [64]),
    ("P14", "Quantos juízes tem o Tribunal Constitucional?", [222]),
    ("P15", "Em que casos pode haver um referendo nacional?", [115]),
    ("P16", "Que direitos nunca podem ser suspensos em estado de emergência?", [19]),
    ("P17", "Portugal pode extraditar alguém para um país onde arrisca a pena de morte?", [33]),
    ("P18", "Quando é que o Presidente não pode dissolver a Assembleia da República?", [172]),
    ("P19", "Qual é a taxa de IVA de um café num restaurante?", []),
    ("P20", "Quem ganhou as últimas eleições legislativas?", []),
]


def posicao(chunks, esperados):
    """Posição (1 a K) do primeiro chunk que contém um artigo esperado; 0 se nenhum contiver."""
    for i, c in enumerate(chunks, start=1):
        artigos = {int(a) for a in c["artigos"].split(",") if a}
        if artigos & set(esperados):
            return i
    return 0


if __name__ == "__main__":
    so_recuperacao = "--so-recuperacao" in sys.argv
    campos = ["id", "pergunta", "esperado", "pos_artigo", "pos_fixo",
              "artigos_rec_artigo", "artigos_rec_fixo",
              "resposta_rag", "resposta_baseline", "tempo_s"]
    hits = {"artigo": [], "fixo": []}
    rr = {"artigo": [], "fixo": []}

    with SAIDA.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=campos, delimiter=";")
        w.writeheader()

        for pid, pergunta, esperados in PERGUNTAS:
            t0 = time.time()
            rec_art = recuperar(pergunta, "crp_artigos", K)
            rec_fix = recuperar(pergunta, "crp_fixos", K)
            linha = {
                "id": pid,
                "pergunta": pergunta,
                "esperado": ",".join(map(str, esperados)) or "—",
                "artigos_rec_artigo": " | ".join(c["artigos"] for c in rec_art),
                "artigos_rec_fixo": " | ".join(c["artigos"] for c in rec_fix),
            }

            if esperados:  # as perguntas fora do âmbito não entram no Hit@5 nem no MRR
                pa, pf = posicao(rec_art, esperados), posicao(rec_fix, esperados)
                linha["pos_artigo"], linha["pos_fixo"] = pa, pf
                for chave, p in (("artigo", pa), ("fixo", pf)):
                    hits[chave].append(1 if p else 0)
                    rr[chave].append(1 / p if p else 0)

            if not so_recuperacao:
                linha["resposta_rag"], _ = responder(pergunta, "crp_artigos", K)
                linha["resposta_baseline"], _ = responder(pergunta, usar_rag=False)

            linha["tempo_s"] = round(time.time() - t0)
            w.writerow(linha)
            f.flush()  # grava já, para não perder nada se o script for interrompido
            print(f"{pid} | posição por artigo={linha.get('pos_artigo', '—')} "
                  f"tamanho fixo={linha.get('pos_fixo', '—')} | {linha['tempo_s']} s")

    media = lambda xs: sum(xs) / len(xs)
    print("\n=== Recuperação (18 perguntas dentro do âmbito) ===")
    for chave in ("artigo", "fixo"):
        print(f"{chave:7} | Hit@{K}: {media(hits[chave]):.0%} | MRR: {media(rr[chave]):.2f}")