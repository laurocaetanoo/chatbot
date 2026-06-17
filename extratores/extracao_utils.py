import re
 
 
def celula(valor):
    if valor is None:
        return ""
    return re.sub(r"\s+", " ", str(valor)).strip()
 
 
def para_int(valor):
    digitos = re.sub(r"\D", "", celula(valor))
    return int(digitos) if digitos else 0
 
 
def limpar_linha(linha):
    return [celula(c) for c in linha if celula(c) != ""]
 
 
def compactar_linha(linha):
    compactadas = []
    for c in linha:
        if c is None:
            continue
        texto = str(c).strip()
        if texto != "":
            compactadas.append(texto)
    return compactadas
 
 
def natureza_vazia(valor):
    return re.sub(r"[-\s]", "", str(valor or "")) == ""
 
 
def normalizar_natureza(valor):
    if natureza_vazia(valor):
        return ""
    texto = celula(valor).replace("0BR", "OBR")
    return texto.replace(" ", "")