import pdfplumber
import re
import os

def extrair_matriz_curricular(caminho_pdf):
    print("-> Executando: extrair_matriz_curricular...")

    if not os.path.exists(caminho_pdf):
        print(f"Erro: O arquivo '{caminho_pdf}' não foi encontrado.")
        return []

    print(f"Iniciando a leitura do arquivo completo: {caminho_pdf}")
    disciplinas_encontradas = []
    semestre_atual = None
    iniciar_extracao = False
    
    MARCADOR_INICIO = "Tabela 9.6: Disciplinas por semestre"
    MARCADOR_FIM = "9.1.6 Disciplinas Optativas"
    regex_semestre = re.compile(r'(\d+)º Semestre')

    try:
        with pdfplumber.open(caminho_pdf) as pdf:
            for i, pagina in enumerate(pdf.pages):
                try:
                    texto_da_pagina = pagina.extract_text(x_tolerance=1, y_tolerance=1)
                except Exception as e_text:
                    print(f"Aviso: Erro ao extrair texto da página {i+1}: {e_text}. Pulando página.")
                    continue 

                if texto_da_pagina is None:
                    continue

                texto_normalizado = re.sub(r'\s+', ' ', texto_da_pagina).strip()

                if not iniciar_extracao and MARCADOR_INICIO in texto_normalizado:
                    print(f"Marcador de início ('{MARCADOR_INICIO}') encontrado na página {i+1}. Iniciando extração.")
                    iniciar_extracao = True

                if iniciar_extracao:
                    tabelas_pagina = []
                    try:
                        tabelas_pagina = pagina.extract_tables()
                    except Exception as e_table:
                        pass 

                    for tabela in tabelas_pagina:
                        for k, linha in enumerate(tabela):
                            if not linha or all(item is None or str(item).strip() == '' for item in linha):
                                continue

                            linha_limpa = [str(item).strip().replace('\n', ' ') for item in linha if item is not None]
                            linha_limpa_filtrada = [item for item in linha_limpa if item] 

                            if not linha_limpa_filtrada: 
                                continue

                            linha_str = " ".join(linha_limpa_filtrada)

                            match_semestre = regex_semestre.search(linha_str)
                            if match_semestre:
                                try:
                                    semestre_atual = int(match_semestre.group(1))
                                    print(f"Encontrado cabeçalho do {semestre_atual}º Semestre na página {i+1}.")
                                except ValueError:
                                    print(f"Aviso: Padrão de semestre encontrado, mas falha na conversão: {match_semestre.group(1)}")
                                continue 

                            if (semestre_atual and len(linha_limpa_filtrada) >= 5 and
                                linha_limpa_filtrada[0] and re.match(r'^[A-Z]\d+$', linha_limpa_filtrada[0])):
                                try:
                                    codigo = linha_limpa_filtrada[0]
                                    nome = linha_limpa_filtrada[1]
                                    ct_str = linha_limpa_filtrada[2]
                                    cp_str = linha_limpa_filtrada[3]
                                    ch_str_raw = linha_limpa_filtrada[4]
                                    
                                    pre_req = linha_limpa_filtrada[5] if len(linha_limpa_filtrada) > 5 else "Nenhum"

                                    ct = int(re.sub(r'\D', '', ct_str)) if ct_str and re.search(r'\d', ct_str) else 0
                                    cp = int(re.sub(r'\D', '', cp_str)) if cp_str and re.search(r'\d', cp_str) else 0
                                    ch_str_clean = re.sub(r'\D', '', str(ch_str_raw))
                                    ch = int(ch_str_clean) if ch_str_clean.isdigit() else 0

                                    if nome.lower() in ["disciplinas", "ct", "cp", "ch", "pré-req", "subtotal"]:
                                        continue

                                    disciplina = {
                                        "semestre": semestre_atual,
                                        "codigo": codigo,
                                        "nome": nome,
                                        "creditos_teoricos": ct,
                                        "creditos_praticos": cp,
                                        "carga_horaria": ch,
                                        "pre_requisitos": pre_req if pre_req and pre_req.strip() else "Nenhum"
                                    }

                                    if disciplina not in disciplinas_encontradas:
                                        disciplinas_encontradas.append(disciplina)

                                except (ValueError, TypeError, IndexError) as e:
                                    print(f"Aviso: Ignorando linha mal formatada na pág {i+1}, linha {k+1} da tabela: {linha_limpa_filtrada} | Erro: {e}")
                                except Exception as e_geral:
                                    print(f"Erro inesperado ao processar linha na pág {i+1}, linha {k+1}: {linha_limpa_filtrada} | Erro: {e_geral}")

                if iniciar_extracao and MARCADOR_FIM in texto_normalizado:
                    print(f"Marcador de fim ('{MARCADOR_FIM}') encontrado na página {i+1}. Encerrando extração.")
                    break 

    except pdfplumber.pdfminer.pdfparser.PDFSyntaxError as e_pdf:
        print(f"Erro de sintaxe ao processar o PDF '{caminho_pdf}': {e_pdf}. Arquivo pode estar corrompido.")
        return []
    except Exception as e_open:
        print(f"Erro geral ao abrir ou processar o PDF '{caminho_pdf}': {e_open}")
        return []

    for disciplina in disciplinas_encontradas:
        disciplina['tipo_info'] = 'matriz_curricular'

    print(f"   -- Extração da Matriz Curricular concluída: {len(disciplinas_encontradas)} disciplinas encontradas.")
    return disciplinas_encontradas

