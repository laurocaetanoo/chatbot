import os
import re
import pdfplumber
 
from .extracao_utils import celula, para_int
 
MARCADOR_INICIO = "Tabela 9.6: Disciplinas por semestre"
PADRAO_FIM = re.compile(r"\b9\.1\.6\b")          
 
PADRAO_SEMESTRE = re.compile(r"(\d+)\s*º\s*Semestre", re.IGNORECASE)
PADRAO_CODIGO = re.compile(r"^[A-Z]\d+$")       
 
TIPO_INFO = "matriz_curricular"
 
def _eh_cabecalho(linha):
    return celula(linha[1]) == "Disciplinas"
 
 
def _eh_subtotal(linha):
    return celula(linha[1]).lower() == "subtotal"
 
 
def _semestre_da_linha(linha):
    m = PADRAO_SEMESTRE.search(celula(linha[0]))
    return int(m.group(1)) if m else None
 
 
def _eh_disciplina(linha):
    return bool(PADRAO_CODIGO.match(celula(linha[0])))
 
 
def _linha_para_disciplina(linha, semestre):
    pre_req = celula(linha[5]) if len(linha) > 5 else ""
    return {
        "semestre": semestre,
        "codigo": celula(linha[0]),
        "nome": celula(linha[1]),
        "creditos_teoricos": para_int(linha[2]),
        "creditos_praticos": para_int(linha[3]),
        "carga_horaria": para_int(linha[4]),
        "pre_requisitos": pre_req if pre_req else "Nenhum",
        "tipo_info": TIPO_INFO,
    }
 
def extrair_matriz_curricular(caminho_pdf):
    if not os.path.exists(caminho_pdf):
        print(f"[erro] Arquivo não encontrado: {caminho_pdf}")
        return []
 
    disciplinas = []
    semestre_atual = None
    extraindo = False
 
    with pdfplumber.open(caminho_pdf) as pdf:
        for num_pagina, pagina in enumerate(pdf.pages, start=1):
            texto = pagina.extract_text(x_tolerance=1, y_tolerance=1) or ""
 
            if not extraindo:
                if MARCADOR_INICIO in texto:
                    extraindo = True
                else:
                    continue  
 
            pagina_final = bool(PADRAO_FIM.search(texto))
 
            for tabela in pagina.extract_tables():
                for linha in tabela:
                    if not linha or _eh_cabecalho(linha) or _eh_subtotal(linha):
                        continue
 
                    semestre = _semestre_da_linha(linha)
                    if semestre is not None:
                        semestre_atual = semestre
                        continue
 
                    if semestre_atual is not None and _eh_disciplina(linha):
                        disciplina = _linha_para_disciplina(linha, semestre_atual)
                        if disciplina not in disciplinas:
                            disciplinas.append(disciplina)
 
            if pagina_final:
                break
 
    print(f"[ok] Matriz curricular: {len(disciplinas)} disciplinas extraídas.")
    return disciplinas
 