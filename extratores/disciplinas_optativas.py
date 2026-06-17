import os
import pdfplumber
 
from .extracao_utils import celula, para_int, limpar_linha 
 
MARCADOR_PAGINA = "Tabela 9.7: Disciplinas Optativas Grupo I"
CARGA_HORARIA_PADRAO = 60  
 
def _linha_para_optativa(linha, grupo):
    cels = limpar_linha(linha)
 
    if len(cels) != 5:
        return None
    
    if cels[0].lower() == "disciplina":
        return None
 
    nome, ct, cp, ch, pre_req = cels
    return {
        "grupo": grupo,
        "nome": nome,
        "creditos_teoricos": para_int(ct),
        "creditos_praticos": para_int(cp),
        "carga_horaria": para_int(ch) or CARGA_HORARIA_PADRAO,
        "pre_requisitos": pre_req if pre_req else "Nenhum",
        "tipo_info": "disciplina_optativa",
    }
 
 
def _parsear_tabela(tabela, grupo):
    if not tabela:
        return []
    disciplinas = []
    for linha in tabela:
        optativa = _linha_para_optativa(linha, grupo)
        if optativa is not None:
            disciplinas.append(optativa)
    return disciplinas
 
 
def _eh_continuacao(tabela):
    if not tabela:
        return False
    primeira = limpar_linha(tabela[0])
    return len(primeira) == 5 and primeira[0].lower() != "disciplina"
 
 
def extrair_disciplinas_optativas(caminho_pdf):
    if not os.path.exists(caminho_pdf):
        print(f"[erro] Arquivo não encontrado: {caminho_pdf}")
        return []
 
    grupo_1, grupo_2 = [], []
 
    with pdfplumber.open(caminho_pdf) as pdf:
        for num_pagina, pagina in enumerate(pdf.pages):
            texto = pagina.extract_text(x_tolerance=2) or ""
            if MARCADOR_PAGINA not in texto:
                continue
 
            tabelas = pagina.extract_tables()
            if len(tabelas) >= 1:
                grupo_1 = _parsear_tabela(tabelas[0], "Grupo I")
            if len(tabelas) >= 2:
                grupo_2 = _parsear_tabela(tabelas[1], "Grupo II")
 
            
            proxima = num_pagina + 1
            if proxima < len(pdf.pages):
                tabelas_prox = pdf.pages[proxima].extract_tables()
                if tabelas_prox and _eh_continuacao(tabelas_prox[0]):
                    grupo_2 += _parsear_tabela(tabelas_prox[0], "Grupo II")
            break
 
    if not grupo_1 and not grupo_2:
        print("[aviso] Não foi possível localizar as tabelas 9.7 / 9.8.")
        return []
 
    saida = grupo_1 + grupo_2
    print(f"[ok] Optativas: Grupo I = {len(grupo_1)}, "
          f"Grupo II = {len(grupo_2)} ({len(saida)} disciplinas).")
    return saida

 
 