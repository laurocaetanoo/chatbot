import os
import re
import pdfplumber
 
from .extracao_utils import celula, para_int, compactar_linha, normalizar_natureza
 
MARCADOR_INICIO = "Optativas - GRUPO 1A"   
PADRAO_GRUPO = re.compile(r"^optativas\s*-\s*grupo", re.IGNORECASE)
 
def _eh_faixa_de_grupo(cels):
    return len(cels) == 1 and bool(PADRAO_GRUPO.match(cels[0]))
 
 
def _linha_para_optativa(cels, grupo):
    if len(cels) != 6:
        return None
 
    disc_2012, ch_2012, nat_2012, disc_2023, ch_2023, nat_2023 = cels
    tem_equivalencia = bool(re.search(r"\d", ch_2023))
 
    return {
        "tipo_info": "equivalencia_optativa",
        "grupo": grupo,
        "disciplina_2012": celula(disc_2012),
        "ch_2012": para_int(ch_2012),
        "nat_2012": normalizar_natureza(nat_2012),
        "disciplina_2023": celula(disc_2023) if tem_equivalencia else "",
        "ch_2023": para_int(ch_2023) if tem_equivalencia else 0,
        "nat_2023": normalizar_natureza(nat_2023) if tem_equivalencia else "",
    }
 
 
def _pagina_inicial(pdf):
    for i, pagina in enumerate(pdf.pages):
        if MARCADOR_INICIO in (pagina.extract_text() or ""):
            return i
    return None
 
 
def extrair_equivalencia_optativas(caminho_pdf):
    if not os.path.exists(caminho_pdf):
        print(f"[erro] Arquivo não encontrado: {caminho_pdf}")
        return []
 
    registros = []
    grupo_atual = "Não especificado"
 
    with pdfplumber.open(caminho_pdf) as pdf:
        inicio = _pagina_inicial(pdf)
        if inicio is None:
            print("[aviso] Seção de optativas (GRUPO 1A) não localizada.")
            return []
 
        for i in range(inicio, len(pdf.pages)):
            for tabela in pdf.pages[i].extract_tables():
                for linha in tabela:
                    cels = compactar_linha(linha)
                    if not cels:
                        continue
 
                    if _eh_faixa_de_grupo(cels):
                        grupo_atual = celula(cels[0])
                        continue
 
                    registro = _linha_para_optativa(cels, grupo_atual)
                    if registro is not None:
                        registros.append(registro)
 
    print(f"[ok] Equivalência (optativas): {len(registros)} disciplinas de 2012.")
    return registros