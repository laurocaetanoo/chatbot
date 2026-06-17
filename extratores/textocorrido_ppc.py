import os
import re
import pdfplumber
 
from .extracao_utils import celula

PAGINAS_SUMARIO = {4, 5}
 
SECOES_RELEVANTES = {
    "IDENTIFICAÇÃO DO CURSO",
    5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18,
    21, 22, 23, 26,
    "ANEXO I",
}
 
PADRAO_NUMERADA = re.compile(r"^(\d{1,2})\.\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ].{2,}$")
PADRAO_ANEXO = re.compile(r"^ANEXO\s+([IVX]+)\b")
TITULO_IDENTIFICACAO = "IDENTIFICAÇÃO DO CURSO"
 
PADRAO_PAGINA = re.compile(r"^\d{1,3}$")
PADRAO_LEGENDA = re.compile(r"^(Tabela|Quadro|Figura)\s+\d+(\.\d+)*\s*[:.]", re.IGNORECASE)
 
 
def _e_ruido(linha):
    l = celula(linha)
    if not l:
        return True

    l = re.sub(r"^\d{1,3}\s+(?=(Tabela|Quadro|Figura)\s)", "", l)
    if PADRAO_PAGINA.match(l):
        return True
    if PADRAO_LEGENDA.match(l):
        return True
    
    tokens = l.split()
    if len(tokens) >= 4 and sum(len(t) == 1 for t in tokens) / len(tokens) > 0.6:
        return True
    return False
 
 
def _eh_tabela_real(tabela_obj):    
    dados = tabela_obj.extract()
    if not dados:
        return False
    linhas_multi = sum(
        1 for linha in dados
        if len([c for c in linha if c and str(c).strip()]) >= 2
    )
    return linhas_multi >= 2
 

def _texto_sem_tabelas(page):
    bboxes = [t.bbox for t in page.find_tables() if _eh_tabela_real(t)]
 
    def fora_das_tabelas(obj):
        x0, top, x1, bottom = obj["x0"], obj["top"], obj["x1"], obj["bottom"]
        for bx0, btop, bx1, bbottom in bboxes:
            if x0 >= bx0 and top >= btop and x1 <= bx1 and bottom <= bbottom:
                return False
        return True
 
    if bboxes:
        page = page.filter(fora_das_tabelas)
    return page.extract_text(x_tolerance=2) or ""
 
 
def _chave_do_titulo(linha, proximo_numero, anexos_vistos):
    norm = celula(linha)
 
    if norm == TITULO_IDENTIFICACAO:
        return TITULO_IDENTIFICACAO
 
    m = PADRAO_NUMERADA.match(norm)
    if m and not re.search(r"\s\d{1,3}$", norm):   
        numero = int(m.group(1))
        if numero == proximo_numero:               
            return numero
 
    a = PADRAO_ANEXO.match(norm)
    if a:
        chave = f"ANEXO {a.group(1)}"
        if chave not in anexos_vistos:
            return chave
 
    return None
 
 
def _remover_fragmentos(texto):
    limpo = re.sub(r"(?:\b[A-Za-zÀ-ÿ]\b[ ]){3,}\b[A-Za-zÀ-ÿ]\b", " ", texto)
    return celula(limpo)
 
 
def extrair_texto_corrido(caminho_pdf):
    if not os.path.exists(caminho_pdf):
        print(f"[erro] Arquivo não encontrado: {caminho_pdf}")
        return []
 
    secoes = {}          
    ordem = []           
    chave_atual = None
    proximo_numero = 1
    anexos_vistos = set()
 
    with pdfplumber.open(caminho_pdf) as pdf:
        for i, page in enumerate(pdf.pages):
            if i in PAGINAS_SUMARIO:
                continue
 
            for linha in _texto_sem_tabelas(page).split("\n"):
                if not linha.strip():
                    continue
 
                chave = _chave_do_titulo(linha, proximo_numero, anexos_vistos)
                if chave is not None:
                    chave_atual = chave
                    if chave not in secoes:
                        secoes[chave] = {"titulo": celula(linha), "linhas": []}
                        ordem.append(chave)
                    if isinstance(chave, int):
                        proximo_numero = chave + 1
                    elif chave.startswith("ANEXO"):
                        anexos_vistos.add(chave)
                    continue
 
                if chave_atual is not None and not _e_ruido(linha):
                    secoes[chave_atual]["linhas"].append(linha.strip())
 
    dados = []
    for chave in ordem:
        if chave not in SECOES_RELEVANTES:
            continue
        texto = _remover_fragmentos(" ".join(secoes[chave]["linhas"]))
        if texto:
            dados.append({
                "tipo_info": "texto_corrido",
                "secao": secoes[chave]["titulo"],
                "texto_bruto": texto,
            })
 
    print(f"[ok] Texto corrido: {len(dados)} seções relevantes extraídas.")
    return dados