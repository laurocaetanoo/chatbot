import os
import re
import pdfplumber
 
from .extracao_utils import celula, para_int, compactar_linha
 
MARCADOR_INICIO = "Disciplinas PPC 2012"   
MARCADOR_FIM = "Optativas - GRUPO"   
 
PADRAO_PERIODO = re.compile(r"\d+º\s*Período", re.IGNORECASE)
CABECALHO_2012 = "disciplinas ppc 2012"
 
def _normalizar_natureza(valor):
    texto = celula(valor).replace("0BR", "OBR")
    return texto
 
 
def _tem_equivalencia(aprov_raw):
    return bool(re.sub(r"[-\s]", "", aprov_raw))
 
 
def _montar_aproveitamento(aprov_raw, ch_raw, nat_raw):
    if not _tem_equivalencia(aprov_raw):
        return []
 
    chs = re.findall(r"\d+", ch_raw)
    n = len(chs)
    if n == 0:
        return []
 
    nats = [s for s in re.split(r"\s+", _normalizar_natureza(nat_raw)) if s]
 
    if n == 1:
        nomes = [celula(aprov_raw)]
    else:
        partes = [p for p in aprov_raw.split("\n") if p.strip()]
        if len(partes) != n:  
            partes = [p for p in re.split(r",", aprov_raw.replace("\n", " ")) if p.strip()]
        nomes = [re.sub(r"\s+", " ", p).strip().strip(",").strip() for p in partes]
 
    equivalencias = []
    for i in range(n):
        equivalencias.append({
            "disciplina": nomes[i] if i < len(nomes) else "",
            "ch": para_int(chs[i]),
            "nat": nats[i] if i < len(nats) else "",
        })
    return equivalencias
 
 
def _linha_para_equivalencia(cels, periodo):
    if len(cels) != 6:
        return None
    if cels[0].strip().lower() == CABECALHO_2012:   
        return None
 
    disc_2012, ch_2012, nat_2012, aprov_2023, ch_2023, nat_2023 = cels
    return {
        "tipo_info": "equivalencia_obrigatoria",
        "periodo": periodo,
        "disciplina_2012": celula(disc_2012),
        "ch_2012": para_int(ch_2012),
        "nat_2012": _normalizar_natureza(nat_2012),
        "aproveitamento_2023": _montar_aproveitamento(aprov_2023, ch_2023, nat_2023),
    }
 
 
def _coletar_paginas_da_matriz(pdf):
    inicio = None
    for i, pagina in enumerate(pdf.pages):
        if MARCADOR_INICIO in (pagina.extract_text() or ""):
            inicio = i
            break
    if inicio is None:
        return []
 
    paginas = []
    for i in range(inicio, len(pdf.pages)):
        texto = pdf.pages[i].extract_text() or ""
        if i != inicio and MARCADOR_FIM in texto:
            break
        paginas.append(i)
    return paginas
 
 
def extrair_equivalencia_obrigatorias(caminho_pdf):
    if not os.path.exists(caminho_pdf):
        print(f"[erro] Arquivo não encontrado: {caminho_pdf}")
        return []
 
    registros = []
    periodo_atual = "Não especificado"
 
    with pdfplumber.open(caminho_pdf) as pdf:
        paginas = _coletar_paginas_da_matriz(pdf)
        if not paginas:
            print("[aviso] ANEXO II (matriz de equivalência) não localizado.")
            return []
 
        for i in paginas:
            for tabela in pdf.pages[i].extract_tables():
                for linha in tabela:
                    cels = compactar_linha(linha)
                    if not cels:
                        continue
 
                    if len(cels) == 1 and PADRAO_PERIODO.search(cels[0]):
                        periodo_atual = celula(cels[0])
                        continue
 
                    registro = _linha_para_equivalencia(cels, periodo_atual)
                    if registro is not None:
                        registros.append(registro)
 
    print(f"[ok] Equivalência (obrigatórias): {len(registros)} disciplinas de 2012.")
    return registros