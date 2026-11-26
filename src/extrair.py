"""
Passo 4 — Extração e limpeza do texto da CRP.

Lê data/raw/CPR.pdf e produz:
  - data/processed/crp_bruto.txt  -> texto tal como sai do PDF, com separadores de página (para inspeção)
  - data/processed/crp_limpo.txt  -> texto limpo, usado no passo 5 (divisão por artigos)

Uso (a partir da raiz do projeto): python src/extrair.py
"""
import re
from collections import Counter
from pathlib import Path

from pypdf import PdfReader

PDF = Path("data/raw/CPR.pdf")
SAIDA_BRUTO = Path("data/processed/crp_bruto.txt")
SAIDA_LIMPO = Path("data/processed/crp_limpo.txt")


def ler_pdf(caminho):
    """Devolve uma lista com o texto de cada página do PDF."""
    reader = PdfReader(caminho)
    paginas = []
    for pagina in reader.pages:
        texto = pagina.extract_text() or ""  # uma página sem texto devolve None
        paginas.append(texto)
    return paginas


def gravar_bruto(paginas, caminho):
    """Grava o texto em bruto, com um separador antes de cada página."""
    resultado = ""
    for n, texto in enumerate(paginas, start=1):
        resultado += f"\n=== PÁGINA {n} ===\n"
        resultado += texto
    caminho.write_text(resultado, encoding="utf-8")


def linhas_repetidas(paginas, limite=0.5):
    """Deteta cabeçalhos e rodapés: linhas curtas que aparecem em mais de metade das páginas."""
    contagem = Counter()
    for texto in paginas:
        linhas_da_pagina = {l.strip() for l in texto.splitlines() if l.strip()}
        contagem.update(linhas_da_pagina)
    minimo = len(paginas) * limite
    return {linha for linha, n in contagem.items() if n >= minimo and len(linha) < 100}


def limpar(paginas):
    """Remove cabeçalhos, rodapés e números de página e normaliza o texto."""
    repetidas = linhas_repetidas(paginas)
    linhas = []
    for texto in paginas:
        for linha in texto.splitlines():
            l = linha.strip()
            if l in repetidas:                 # cabeçalho ou rodapé
                continue
            if re.fullmatch(r"\d{1,3}", l):    # número de página solto
                continue
            linhas.append(l)

    texto = "\n".join(linhas)
    texto = re.sub(r"(\w)-\n(\w)", r"\1\2", texto)  # junta palavras cortadas por hífen
    texto = re.sub(r"[ \t]+", " ", texto)            # espaços repetidos
    texto = re.sub(r"\n{3,}", "\n\n", texto)         # linhas em branco a mais
    return texto.strip(), repetidas


if __name__ == "__main__":
    paginas = ler_pdf(PDF)
    print("Páginas lidas:", len(paginas))

    gravar_bruto(paginas, SAIDA_BRUTO)

    limpo, repetidas = limpar(paginas)
    SAIDA_LIMPO.write_text(limpo, encoding="utf-8")

    # Verificações
    print("\nLinhas removidas como cabeçalho/rodapé:")
    for l in sorted(repetidas):
        print("  -", l)

    artigos = re.findall(r"^Artigo \d+\.\s?[º°o]", limpo, flags=re.MULTILINE)
    print(f"\nTítulos 'Artigo N.º' encontrados: {len(artigos)} (a CRP tem 296)")