import os
import pdfplumber
 
from .extracao_utils import celula, limpar_linha
 
TITULO_TABELA = "Quadro 19.1 - Docentes do DComp"
MARCADOR = "Professor(a)"        
CABECALHO_NOME = "professor(a)"
 
CATEGORIAS = {
    "EBTT": "Ensino Básico, Técnico e Tecnológico",
    "MS": "Magistério Superior",
}
REGIMES = {
    "DE": "Dedicação Exclusiva",
    "20h": "Tempo parcial (20 horas)",
    "40h": "Tempo parcial (40 horas)",
}
 
 
def _eh_linha_de_dados(cels):
    return len(cels) == 4 and cels[0].strip().lower() != CABECALHO_NOME
 
 
def _linha_para_docente(cels):
    nome, titulacao, categoria_sigla, regime_sigla = (celula(c) for c in cels)
    return {
        "tipo_info": "corpo_docente_individual",
        "nome": nome,
        "titulacao": titulacao,
        "categoria_sigla": categoria_sigla,
        "categoria_full": CATEGORIAS.get(categoria_sigla, categoria_sigla),
        "regime_sigla": regime_sigla,
        "regime_full": REGIMES.get(regime_sigla, regime_sigla),
    }
 
 
def _pagina_da_tabela(pdf):
    for i, pagina in enumerate(pdf.pages):
        if MARCADOR in (pagina.extract_text() or ""):
            return i
    return None
 
 
def extrair_dados_corpo_docente(caminho_pdf):
    if not os.path.exists(caminho_pdf):
        print(f"[erro] Arquivo não encontrado: {caminho_pdf}")
        return []
 
    docentes = []
 
    with pdfplumber.open(caminho_pdf) as pdf:
        pagina = _pagina_da_tabela(pdf)
        if pagina is None:
            print("[aviso] Quadro 19.1 (corpo docente) não localizado.")
            return []
 
        for tabela in pdf.pages[pagina].extract_tables():
            for linha in tabela:
                cels = limpar_linha(linha)
                if _eh_linha_de_dados(cels):
                    docentes.append(_linha_para_docente(cels))
 
    if not docentes:
        print("[aviso] Nenhum docente extraído do Quadro 19.1.")
        return []
 
    print(f"[ok] Corpo docente: {len(docentes)} docentes.")
    return docentes
 