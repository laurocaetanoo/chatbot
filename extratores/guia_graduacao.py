import os
import re
 
import fitz 
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
 
PAGINAS_IGNORADAS = {1, 2, 3, 4, 22, 23, 24, 25, 26, 27, 28, 29, 35}
MIN_CHARS_CORPO = 80         
 
MARCADOR_COORDENADORES = "COORDENADORES"
MARCADOR_DEPARTAMENTOS = "DEPARTAMENTOS"
 
CABECALHOS_PAGINA = {
    "informações pedagógicas", "informações acadêmicas", "pedagógicas",
    "acadêmicas", "informações", "programas da assistência estudantil",
    "nossos cursos", "conheça nossos cursos", "saiba mais", "importante",
}
 
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1500,
    chunk_overlap=150,
    separators=["\n\n", "\n", ". ", "? ", "! ", "; ", " ", ""],
)
 
  
PADROES_RUIDO = [
    r"Conheça a página[^\n]*",
    r"da biblioteca[^\n]*",
    r"Leia a Resolução[^\n]*",
]
 
def _juntar_letras_espacadas(texto):
    return re.sub(r"(?:\b\w\b )(?:\b\w\b ?){2,}",
                  lambda m: m.group(0).replace(" ", ""), texto)
 
 
def _limpar(texto):
    texto = _juntar_letras_espacadas(texto)
    texto = re.sub(r"-\s*\n", "", texto)          
    texto = re.sub(r"\s*\n\s*", " ", texto)       
    for padrao in PADROES_RUIDO:
        texto = re.sub(padrao, "", texto, flags=re.IGNORECASE)
    return re.sub(r"\s{2,}", " ", texto).strip()
 
  
def _extrair_coordenadores(page, pagina):
    words = page.get_text("words")  
    emails = [w for w in words if "ifma.edu.br" in w[4] and "@" in w[4]]
 
    chunks = []
    for em in emails:
        ex, ey = (em[0] + em[2]) / 2, em[1]
        acima, abaixo = [], []
        for w in words:
            if w is em or "@" in w[4]:
                continue
            if abs((w[0] + w[2]) / 2 - ex) > 180:
                continue
            dy = w[1] - ey
            if -130 < dy < -5:
                acima.append((w[1], w[0], w[4]))
            elif 5 < dy < 130:
                abaixo.append((w[1], w[0], w[4]))
 
        nome = " ".join(t for _, _, t in sorted(acima))
        curso = " ".join(t for _, _, t in sorted(abaixo))
        if not (nome and curso):
            continue
        page_content = (
            f"O coordenador do curso de {curso} é {nome}. "
            f"Para contato com a coordenação do curso de {curso}, o e-mail é {em[4]}. "
            f"O e-mail da coordenação do curso de {curso} é {em[4]}. "
            f"Para falar com a coordenação ou com o coordenador de {curso}, "
            f"utilize o e-mail de contato {em[4]}."
        )
        chunks.append({
            "page_content": page_content,
            "metadata": {"source": "Guia da Graduação",
                         "secao": f"Coordenador de {curso}", "page": pagina},
        })
    return chunks
 
  
def _extrair_departamentos(page, pagina):
    linhas = [l.strip() for l in page.get_text().splitlines() if l.strip()]
    chunks = []
    i = 0
    while i < len(linhas) - 1:
        nome, abaixo = linhas[i], linhas[i + 1]
        if nome.startswith("Departamento") and "@ifma" in abaixo:
            chunks.append({
                "page_content": f"O {nome} pode ser contatado pelo e-mail {abaixo}.",
                "metadata": {"source": "Guia da Graduação", "secao": nome, "page": pagina},
            })
            i += 2
        else:
            i += 1
    return chunks
 
  
def _blocos_texto(page):
    out = []
    for b in page.get_text("blocks"):
        x0, y0, x1, y1, texto, _, tipo = b
        if tipo != 0:
            continue
        limpo = _limpar(texto)
        if limpo and limpo.lower() not in CABECALHOS_PAGINA:
            out.append({"x0": x0, "y0": y0, "x1": x1, "y1": y1,
                        "cx": (x0 + x1) / 2, "texto": limpo})
    return out
 
 
GAP_CARD = 80
FRONTEIRA_COLUNA = 450
 
 
def _agrupar_em_cards(blocos):
    cards = []
    for esquerda in (True, False):
        coluna = sorted(
            [b for b in blocos if (b["cx"] < FRONTEIRA_COLUNA) == esquerda],
            key=lambda b: b["y0"],
        )
        atual = None
        for b in coluna:
            if atual is not None and (b["y0"] - atual[-1]["y1"]) < GAP_CARD:
                atual.append(b)
            else:
                atual = [b]
                cards.append(atual)
    return cards
 
 
def _extrair_narrativa(page, pagina, pdf_path):
    blocos = _blocos_texto(page)
    cards = _agrupar_em_cards(blocos)
 
    chunks = []
    for card in cards:
        card.sort(key=lambda b: (round(b["y0"]), b["x0"]))
        texto = " ".join(b["texto"] for b in card)
        texto = re.sub(r"\s{2,}", " ", texto).strip()
        if len(texto) < MIN_CHARS_CORPO:
            continue
        secao = " ".join(texto.split()[:6])
        doc = Document(page_content=texto,
                       metadata={"source": pdf_path, "secao": secao[:60], "page": pagina})
        for j, parte in enumerate(splitter.split_documents([doc])):
            md = dict(parte.metadata)
            md["chunk_id"] = f"page_{pagina}_block_{secao[:20]}_{j}"
            chunks.append({"page_content": parte.page_content, "metadata": md})
    return chunks
 
  
def extrair_chunks_guia_graduacao(pdf_path):
    print(f"-> Extraindo Guia da Graduação ({pdf_path})...")
    if not os.path.exists(pdf_path):
        print(f"   [erro] Arquivo não encontrado: {pdf_path}")
        return []
 
    chunks = []
    try:
        doc = fitz.open(pdf_path)
        for i, page in enumerate(doc, start=1):
            if i in PAGINAS_IGNORADAS:
                continue
            texto = page.get_text()
            if MARCADOR_COORDENADORES in texto:
                chunks.extend(_extrair_coordenadores(page, i))
            elif MARCADOR_DEPARTAMENTOS in texto:
                chunks.extend(_extrair_departamentos(page, i))
            else:
                chunks.extend(_extrair_narrativa(page, i, pdf_path))
        doc.close()
    except Exception as e:
        print(f"   [erro] Falha ao processar '{pdf_path}': {e}")
        return []
 
    print(f"[ok] Guia da Graduação: {len(chunks)} chunks extraídos.")
    return chunks