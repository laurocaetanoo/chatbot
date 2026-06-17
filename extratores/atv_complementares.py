import os
import re
import pdfplumber
 
from .extracao_utils import celula, compactar_linha
 
ASSINATURA_TABELA = "CH Máxima"
TITULO = "Quadro 1"                         
COLUNA_ITEM = "item"                        
PADRAO_ROMANO = re.compile(r"^[IVX]+$")     
 
 
def _eh_titulo(texto):
    return texto.strip().lower().startswith(TITULO.lower())
 
 
def _eh_linha_de_dados(cels):
    return len(cels) == 4 and bool(PADRAO_ROMANO.match(cels[0].strip()))
 
 
def _eh_cabecalho_coluna(cels):
    return len(cels) == 4 and cels[0].strip().lower() == COLUNA_ITEM
 
 
def _linha_para_atividade(cels, grupo):
    item, atividade, carga_horaria, ch_maxima = (celula(c) for c in cels)
    return {
        "tipo_info": "atividades_complementares",
        "grupo": grupo,
        "item": item,
        "atividade": atividade,
        "carga_horaria": carga_horaria,
        "ch_maxima": ch_maxima,
    }
 
 
def _paginas_da_tabela(pdf):
    return [i for i, p in enumerate(pdf.pages)
            if ASSINATURA_TABELA in (p.extract_text() or "")]
 
 
def extrair_atividades_complementares(caminho_pdf):
    if not os.path.exists(caminho_pdf):
        print(f"[erro] Arquivo não encontrado: {caminho_pdf}")
        return []
 
    atividades = []
    grupo_atual = "Não especificado"
 
    with pdfplumber.open(caminho_pdf) as pdf:
        paginas = _paginas_da_tabela(pdf)
        if not paginas:
            print("[aviso] Quadro 1 (atividades complementares) não localizado.")
            return []
 
        for i in paginas:
            for tabela in pdf.pages[i].extract_tables():
                for linha in tabela:
                    cels = compactar_linha(linha)
                    if not cels:
                        continue
 
                    if len(cels) == 1:
                        if not _eh_titulo(cels[0]):
                            grupo_atual = celula(cels[0])
                        continue
 
                    if _eh_cabecalho_coluna(cels):
                        continue
 
                    if _eh_linha_de_dados(cels):
                        atividades.append(_linha_para_atividade(cels, grupo_atual))
 
    categorias = []
    for a in atividades:
        if a["grupo"] not in categorias:
            categorias.append(a["grupo"])
 
    print(f"[ok] Atividades complementares: {len(atividades)} atividades "
          f"em {len(categorias)} categorias.")
    return atividades