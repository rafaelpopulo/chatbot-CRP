"""
Passos 5, 6 e 7 — Divisão do texto da CRP em chunks e estatísticas do corpus.

Lê data/processed/crp_limpo.txt e produz:
  - data/processed/artigos.json      -> 1 chunk por artigo (chunking estruturado)
  - data/processed/chunks_fixos.json -> chunks de tamanho fixo (para comparação)

Uso (a partir da raiz do projeto): python src/chunking.py
"""
import json
import re
from pathlib import Path

ENTRADA = Path("data/processed/crp_limpo.txt")
SAIDA_ARTIGOS = Path("data/processed/artigos.json")
SAIDA_FIXOS = Path("data/processed/chunks_fixos.json")

TAMANHO_FIXO = 800   # caracteres por chunk
SOBREPOSICAO = 100   # caracteres repetidos entre chunks seguidos

# "Artigo 24.º" no início da linha (com ou sem a epígrafe na mesma linha)
RE_ARTIGO = re.compile(r"^Artigo (\d+)\.\s?[º°o]\s*(.*)$")
# Divisões da Constituição: PARTE I, TÍTULO II, CAPÍTULO III, SECÇÃO I...
RE_DIVISAO = re.compile(r"^(PARTE|TÍTULO|CAPÍTULO|SECÇÃO)\s+([IVXLC]+|ÚNICO|ÚNICA)\b")

NIVEIS = ["parte", "titulo", "capitulo", "seccao"]
NIVEL_POR_PALAVRA = {"PARTE": "parte", "TÍTULO": "titulo", "CAPÍTULO": "capitulo", "SECÇÃO": "seccao"}


def formatar_corpo(linhas):
    """Junta as linhas partidas pelo PDF, mas põe cada número (1., 2.) e alínea (a), b)) na sua linha."""
    texto = re.sub(r"\s+", " ", " ".join(linhas)).strip()
    texto = re.sub(r" (?=\d{1,2}\. )", "\n", texto)     # novo número do artigo
    texto = re.sub(r" (?=[a-z]{1,2}\) )", "\n", texto)  # nova alínea
    return texto


def dividir_por_artigo(texto):
    """Percorre o texto linha a linha e separa-o em artigos, guardando onde cada um está na CRP."""
    artigos = []
    estrutura = {n: "" for n in NIVEIS}  # Parte/Título/Capítulo/Secção em que estamos
    atual = None                         # artigo que está a ser lido
    espera = None                        # o que a próxima linha deve ser: "epigrafe" ou o nome de uma divisão

    def fechar():
        if atual:
            atual["corpo"] = formatar_corpo(atual.pop("linhas"))
            artigos.append(atual)

    for linha in texto.splitlines():
        l = linha.strip()
        if not l:
            continue

        m_art = RE_ARTIGO.match(l)
        m_div = RE_DIVISAO.match(l)

        if m_art:                                    # começa um artigo novo
            fechar()
            atual = {"numero": int(m_art.group(1)), "epigrafe": "", "linhas": [], **estrutura}
            resto = m_art.group(2).strip()
            if resto:
                atual["epigrafe"] = resto.strip("()")
                espera = None
            else:
                espera = "epigrafe"

        elif m_div:                                  # começa uma Parte, Título, Capítulo ou Secção
            fechar()
            atual = None
            nivel = NIVEL_POR_PALAVRA[m_div.group(1)]
            estrutura[nivel] = m_div.group(0)
            for n in NIVEIS[NIVEIS.index(nivel) + 1:]:   # os níveis abaixo recomeçam
                estrutura[n] = ""
            resto = l[m_div.end():].strip()
            if resto:
                estrutura[nivel] += " — " + resto
                espera = None
            else:
                espera = nivel

        elif l.lower() == "princípios fundamentais":  # bloco inicial (art. 1.º a 11.º)
            fechar()
            atual = None
            estrutura = {n: "" for n in NIVEIS}
            estrutura["parte"] = "Princípios fundamentais"
            espera = None

        elif espera == "epigrafe" and atual:         # linha a seguir a "Artigo N.º"
            atual["epigrafe"] = l.strip("()")
            espera = None

        elif espera in NIVEIS:                       # nome da divisão (ex.: "Direitos e deveres fundamentais")
            estrutura[espera] += " — " + l
            espera = None

        elif atual:                                  # texto do artigo
            atual["linhas"].append(l)

    fechar()
    return artigos


def dividir_tamanho_fixo(texto, tamanho, sobreposicao):
    """Corta o texto em pedaços de tamanho fixo e regista que artigos cada pedaço contém."""
    plano = re.sub(r"\s+", " ", texto).strip()

    # Onde começa cada artigo no texto corrido (só aceita números seguidos: 1, 2, 3...)
    inicios = []
    for m in re.finditer(r"Artigo (\d+)\.\s?[º°o]", plano):
        numero = int(m.group(1))
        if numero == len(inicios) + 1:
            inicios.append(m.start())
    limites = [(inicios[i], inicios[i + 1] if i + 1 < len(inicios) else len(plano), i + 1)
               for i in range(len(inicios))]

    chunks = []
    inicio = 0
    while inicio < len(plano):
        fim = min(inicio + tamanho, len(plano))
        if fim < len(plano):                          # não cortar palavras a meio
            espaco = plano.rfind(" ", inicio, fim)
            if espaco > inicio:
                fim = espaco
        contidos = [num for a, b, num in limites if a < fim and b > inicio]
        chunks.append({
            "id": f"fix_{len(chunks):03d}",
            "artigos": ",".join(map(str, contidos)),
            "texto": plano[inicio:fim],
        })
        if fim == len(plano):
            break
        inicio = fim - sobreposicao
    return chunks


if __name__ == "__main__":
    texto = ENTRADA.read_text(encoding="utf-8")

    # --- Passo 5: por artigo ---
    artigos = []
    for a in dividir_por_artigo(texto):
        artigos.append({
            "id": f"art_{a['numero']:03d}",
            "numero": a["numero"],
            "epigrafe": a["epigrafe"],
            "parte": a["parte"],
            "titulo": a["titulo"],
            "capitulo": a["capitulo"],
            "seccao": a["seccao"],
            "artigos": str(a["numero"]),
            "texto": f"Artigo {a['numero']}.º — {a['epigrafe']}\n{a['corpo']}",
        })
    SAIDA_ARTIGOS.write_text(json.dumps(artigos, ensure_ascii=False, indent=2), encoding="utf-8")

    # --- Passo 6: tamanho fixo ---
    fixos = dividir_tamanho_fixo(texto, TAMANHO_FIXO, SOBREPOSICAO)
    SAIDA_FIXOS.write_text(json.dumps(fixos, ensure_ascii=False, indent=2), encoding="utf-8")

    # --- Verificações ---
    numeros = [a["numero"] for a in artigos]
    print(f"Artigos: {len(artigos)} (esperado: 296)")
    print("Em falta:", sorted(set(range(1, 297)) - set(numeros)) or "nenhum")
    print("Repetidos:", sorted({n for n in numeros if numeros.count(n) > 1}) or "nenhum")
    print("Sem epígrafe:", sum(1 for a in artigos if not a["epigrafe"]))
    print("Sem Parte identificada:", sum(1 for a in artigos if not a["parte"]))
    print(f"Chunks de tamanho fixo: {len(fixos)}")

    # --- Passo 7: estatísticas do corpus ---
    tamanhos = sorted(((len(a["texto"]), a["numero"]) for a in artigos), reverse=True)
    media = sum(t for t, _ in tamanhos) / len(tamanhos)
    print(f"\nTamanho médio de um artigo: {media:.0f} caracteres")
    print(f"Mais curto: {tamanhos[-1][0]} caracteres (art. {tamanhos[-1][1]}.º)")
    print("5 mais longos:", ", ".join(f"art. {n}.º ({t})" for t, n in tamanhos[:5]))

    print("\nExemplo — artigo 24.º:")
    print(next(a["texto"] for a in artigos if a["numero"] == 24))