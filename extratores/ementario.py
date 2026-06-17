import os
import re
import pdfplumber
 
from .extracao_utils import celula, compactar_linha
 
ASSINATURA = "Ementa:"   
 
PADRAO_CREDITOS = re.compile(r"^Créditos")
PADRAO_PRE_REQ = re.compile(r"^Pré-requisito")
BIBLIO_BASICA = "Bibliografia Básica"
BIBLIO_COMPLEMENTAR = "Bibliografia Complementar"
 
PADRAO_REFERENCIA = re.compile(r"^[A-ZÀ-Ý][A-ZÀ-Ý.'\-]+,")
 
def _vazio_ou_traco(texto):
    return re.sub(r"[-\s]", "", texto) == ""
 
 
def _split_referencias(texto_celula):
    referencias = []
    for linha in texto_celula.split("\n"):
        linha = linha.strip()
        if not linha:
            continue
        if PADRAO_REFERENCIA.match(linha) or not referencias:
            referencias.append(linha)
        else:
            referencias[-1] += " " + linha
    return referencias
 
 
def _rotulo_da_linha(cels):
    primeira = cels[0].strip()
    extra = " ".join(celula(c) for c in cels[1:])
 
    if primeira.startswith("Objetivo:"):
        inicio = re.sub(r"^Objetivo:\s*", "", celula(cels[0]))
        return "objetivo", f"{inicio} {extra}".strip()
    if primeira.startswith("Ementa:"):
        inicio = re.sub(r"^Ementa:\s*", "", celula(cels[0]))
        return "ementa", f"{inicio} {extra}".strip()
    if primeira == BIBLIO_BASICA:
        return "bib_basica", ""
    if primeira == BIBLIO_COMPLEMENTAR:
        return "bib_complementar", ""
    return None
 
 
def _acumular(disc, campo, texto_raw):
    if campo in ("objetivo", "ementa"):
        texto = celula(texto_raw)
        if texto:
            disc[campo] = f"{disc[campo]} {texto}".strip()
    else:
        texto = texto_raw.strip()
        if texto:
            chave = "_bib_basica_raw" if campo == "bib_basica" else "_bib_complementar_raw"
            disc[chave] = f"{disc[chave]}\n{texto}".strip() if disc[chave] else texto
 
 
def _nova_disciplina(nome):
    return {
        "tipo_info": "ementario",
        "disciplina": nome,
        "creditos": "",
        "carga_horaria": "",
        "departamento": "",
        "pre_requisitos": "Nenhum",
        "objetivo": "",
        "ementa": "",
        "bibliografia_basica": [],
        "bibliografia_complementar": [],
        "_bib_basica_raw": "",          
        "_bib_complementar_raw": "",
    }
 
 
def _finalizar(disc):
    disc["bibliografia_basica"] = _split_referencias(disc.pop("_bib_basica_raw"))
    disc["bibliografia_complementar"] = _split_referencias(disc.pop("_bib_complementar_raw"))
    return disc
 
 
def _coletar_linhas(pdf):
    paginas = [i for i, p in enumerate(pdf.pages)
               if ASSINATURA in (p.extract_text() or "")]
    if not paginas:
        return []
 
    linhas = []
    for i in range(min(paginas), max(paginas) + 1):
        for tabela in pdf.pages[i].extract_tables():
            for linha in tabela:
                cels = compactar_linha(linha)
                if cels:
                    linhas.append(cels)
    return linhas
 
 
def extrair_ementario(caminho_pdf):
    if not os.path.exists(caminho_pdf):
        print(f"[erro] Arquivo não encontrado: {caminho_pdf}")
        return []
 
    with pdfplumber.open(caminho_pdf) as pdf:
        linhas = _coletar_linhas(pdf)
 
    if not linhas:
        print("[aviso] Ementário não localizado.")
        return []
 
    disciplinas = []
    atual = None
    campo_atual = None   
 
    for idx, cels in enumerate(linhas):
        primeira = cels[0]
        proxima = linhas[idx + 1] if idx + 1 < len(linhas) else None
 
        eh_nome = (len(cels) == 1 and proxima is not None
                   and PADRAO_CREDITOS.match(proxima[0]))
        if eh_nome:
            if atual is not None:
                disciplinas.append(_finalizar(atual))
            atual = _nova_disciplina(celula(primeira))
            campo_atual = None
            continue
 
        if atual is None:
            continue  
 
        if PADRAO_CREDITOS.match(primeira) and len(cels) >= 6:
            atual["creditos"] = celula(cels[1])
            atual["carga_horaria"] = celula(cels[3])
            atual["departamento"] = celula(cels[5])
            campo_atual = None
            continue
        if PADRAO_PRE_REQ.match(primeira):
            valor = celula(cels[1]) if len(cels) > 1 else ""
            atual["pre_requisitos"] = "Nenhum" if _vazio_ou_traco(valor) else valor
            campo_atual = None
            continue
 
        rotulo = _rotulo_da_linha(cels)
        if rotulo is not None:
            campo_atual, texto_inicial = rotulo
            _acumular(atual, campo_atual, texto_inicial)
            continue
 
        if campo_atual is not None:
            _acumular(atual, campo_atual, "\n".join(str(c) for c in cels if c))
 
    if atual is not None:
        disciplinas.append(_finalizar(atual))
 
    print(f"[ok] Ementário: {len(disciplinas)} disciplinas extraídas.")
    return disciplinas