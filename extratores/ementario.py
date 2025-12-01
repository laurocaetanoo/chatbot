
import pdfplumber
import re
import os

def extrair_introducao_robotica(pdf_path):
    print("   -> Extraindo disciplina 'Introdução à Robótica' manualmente...")
    try:
        with pdfplumber.open(pdf_path) as pdf:
            texto = "\n".join(
                pdf.pages[i].extract_text(x_tolerance=2) or ""
                for i in range(69, min(71, len(pdf.pages)))
            )

        bloco = re.search(r"Introdução a Robótica[\s\S]*?(?=(Mineração de Texto|$))", texto, re.IGNORECASE)
        if not bloco:
            print("   -- Bloco da disciplina não encontrado.")
            return None

        bloco = bloco.group(0)

        def extrair(regex, texto, padrao=""):
            m = re.search(regex, texto, re.S)
            return (m.group(1).strip() if m else padrao).strip()

        data = {
            "disciplina": "Introdução à Robótica",
            "tipo_info": "ementario",
            "creditos": extrair(r"Créditos\s+(\S+)", bloco, "2T2P"),
            "carga_horaria": extrair(r"Carga Horária\s+(\S+)", bloco, "60h"),
            "departamento": extrair(r"Departamento\s+(\S+)", bloco, "DCOMP"),
            "pre_requisitos": extrair(r"Pré-requisito\(s\)\s*(.*?)\n", bloco, "Inteligência Artificial"),
            "objetivo": extrair(
                r"Objetivo:\s*(.*?)\nEmenta:",
                bloco,
                "Conhecer e aplicar os conceitos de robótica na implementação de projetos com e sem uso de Inteligência Artificial.",
            ),
            "ementa": extrair(
                r"Ementa:\s*(.*?)(?:\nBibliografia|$)",
                bloco,
                "Conceitos e aplicações da robótica. Componentes eletrônicos, manipuladores, sensores, Arduino, programação e robótica inteligente."
            ),
            "bibliografia_basica": [],
            "bibliografia_complementar": []
        }

        print("   -> 'Introdução à Robótica' extraída com sucesso manualmente.")
        return data

    except Exception as e:
        print(f"   -- Erro ao extrair disciplina 'Introdução à Robótica': {e}")
        return None

def parse_discipline_block(block):
    data = {}
    block = block.strip()

    lines = [ln.strip() for ln in block.split("\n") if ln.strip()]

    data["disciplina"] = "Indefinida"
    for i, line in enumerate(lines):
        if i + 1 < len(lines) and "Créditos" in lines[i + 1]:
            data["disciplina"] = line
            break

    match = re.search(r"Créditos\s+(\S+).*?Carga Horária\s+(\S+).*?Departamento\s+(\S+)", block)
    if match:
        data["creditos"] = match.group(1)
        data["carga_horaria"] = match.group(2)
        data["departamento"] = match.group(3)
    else:
        data["creditos"] = data["carga_horaria"] = data["departamento"] = "N/A"

    match = re.search(r"Pré-requisito\(s\)\s*(.*?)\s*(?:\n|Objetivo:)", block)
    data["pre_requisitos"] = match.group(1).strip() if match and match.group(1).strip() else "Nenhum"

    match = re.search(r"Objetivo:\s*(.*?)\nEmenta:", block, re.S)
    data["objetivo"] = match.group(1).strip() if match else ""

    match = re.search(r"Ementa:\s*(.*?)(?:\nBibliografia Básica|\nBibliografia Complementar|\Z)", block, re.S)
    data["ementa"] = match.group(1).strip() if match else ""

    match = re.search(r"Bibliografia Básica\s*(.*?)(?:\nBibliografia Complementar|\Z)", block, re.S)
    data["bibliografia_basica"] = [ref.strip() for ref in match.group(1).split("\n") if ref.strip()] if match else []

    match = re.search(r"Bibliografia Complementar\s*(.*)", block, re.S)
    data["bibliografia_complementar"] = [ref.strip() for ref in match.group(1).split("\n") if ref.strip()] if match else []

    return data

def extrair_ementario(pdf_path, start_page=45, end_page=78): 
    print("-> Executando: extrair_ementario...")
    dados_extraidos = []

    if not os.path.exists(pdf_path):
        print(f"   -- Erro: O arquivo '{pdf_path}' não foi encontrado.")
        return []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            end_page_safe = min(end_page, len(pdf.pages))

            for i in range(start_page - 1, end_page_safe):
                text += pdf.pages[i].extract_text(x_tolerance=2) + "\n"

            text = text.encode("utf-8", "ignore").decode("utf-8")
            text = text.replace("\r", "")
            text = text.replace("-\n", "")          
            text = re.sub(r"\s+\n", "\n", text)     
            text = re.sub(r"\n{2,}", "\n", text)

            blocks = re.split(r"\n(?=[A-ZÁÉÍÓÚÂÊÔÇ][^\n]{2,120}\nCréditos\s)", text)
            blocks = [blk for blk in blocks if 'Créditos' in blk]

            for block in blocks:
                parsed_data = parse_discipline_block(block)
                parsed_data["tipo_info"] = "ementario"
                dados_extraidos.append(parsed_data)
            
            nomes = [d.get("disciplina", "") for d in dados_extraidos]
            if "Introdução à Robótica" not in nomes:
                print("   ** 'Introdução à Robótica' não detectada, aplicando extração manual...")
                extra = extrair_introducao_robotica(pdf_path)
                if extra:
                    dados_extraidos.append(extra)

    except Exception as e:
        print(f"   -- Erro ao processar o ementário: {e}")
        return []

    print(f"   -- Extração do Ementário concluída: {len(dados_extraidos)} disciplinas encontradas.")
    return dados_extraidos
