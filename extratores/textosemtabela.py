
import pdfplumber
import re
import os

def normalize_string(s):
    s = re.sub(r'\s+', ' ', s)
    return s.strip()

def tratar_pagina_29_excecao(pdf_path):
    print("    -- Aplicando regra de exceção para a página 29...")
    conteudo_excecao = {}

    try:
        with pdfplumber.open(pdf_path) as pdf:
            if len(pdf.pages) <= 28:
                print("    -- AVISO: Página 29 não encontrada na exceção.")
                return {}

            page = pdf.pages[28]  
            texto_pagina = page.extract_text(x_tolerance=2) or ""

            marcador_inicio = "9.1.6 Disciplinas Optativas"
            start_index = texto_pagina.find(marcador_inicio)

            if start_index != -1:
                bloco = texto_pagina[start_index:]
                secao = "9.1.6 Disciplinas Optativas"
                conteudo_excecao[secao] = bloco.strip()
            else:
                print("    -- AVISO: Marcador '9.1.6 Disciplinas Optativas' não encontrado na página 29.")
    except Exception as e:
        print(f"    -- Erro na exceção da página 29: {e}")
        return {}

    return conteudo_excecao


def extrair_texto_corrido_por_topicos(pdf_path, paginas_pular=None):
    if paginas_pular is None:
        paginas_pular = [4, 5, 28]

    topicos_importantes = [
        "IDENTIFICAÇÃO DO CURSO", 
        "5. Perfil Profissional do Egresso",
        "6. Formas de Ingresso",
        "7. Políticas Institucionais no Âmbito do Curso",
        "8. Apoio ao Discente",
        "9. Organização Didático-Pedagógica",
        "10. Metodologia de Ensino",
        "11. Estágio Obrigatório",
        "12. Trabalho de Conclusão de Curso (TCC)",
        "13. Prática de Componentes Curriculares",
        "14. Atividades Curriculares de Extensão",
        "15. Atividades Complementares",
        "16. Critérios de aproveitamento de conhecimentos e experiências",
        "17. Avaliação da Aprendizagem",
        "18. Avaliação do Curso",
        "21. Núcleo Docente Estruturante (NDE)",
        "22. Colegiado do Curso",
        "23. Coordenação de Curso",
        "26. Certificação e Diploma",
        "ANEXO I - REGULAMENTO DAS ATIVIDADES COMPLEMENTARES"
    ]

    topicos_irrelevantes = [
        "1. Apresentação",
        "2. Histórico da Instituição",
        "3. Justificativa",
        "4. Objetivos",
        "19. Ementário e Bibliografias",
        "20. Corpo Docente e Corpo Administrativo",
        "24. Infraestrutura",
        "25. Acervo",
        "27. Referências"
    ]

    conteudo_extraido = {}
    secao_atual = None
    capturando = False
    topico_pai_atual = None  

    todos_os_topicos = topicos_importantes + topicos_irrelevantes
    topicos_normalizados = {normalize_string(t): t for t in todos_os_topicos}

    prefixos_topicos_importantes = [t.split()[0].rstrip('.') for t in topicos_importantes if t[0].isdigit()] 

    with pdfplumber.open(pdf_path) as pdf:
        print(f"    -- Páginas a serem puladas (índices): {paginas_pular}")
        for i, page in enumerate(pdf.pages):
            if i in paginas_pular:
                print(f"    -- Pulando página {i+1} (índice {i})")
                continue
            print(f"    -- Processando página {i+1} (índice {i})")

            tables = page.find_tables()
            table_bboxes = [table.bbox for table in tables]

            def is_outside_tables(obj):
                def is_within_bbox(obj, bbox):
                    obj_bbox = (obj["x0"], obj["top"], obj["x1"], obj["bottom"])
                    return (obj_bbox[0] >= bbox[0] and obj_bbox[1] >= bbox[1] and
                            obj_bbox[2] <= bbox[2] and obj_bbox[3] <= bbox[3])
                return not any(is_within_bbox(obj, bbox) for bbox in table_bboxes)

            page_sem_tabelas = page.filter(is_outside_tables)
            texto_pagina = page_sem_tabelas.extract_text(x_tolerance=2, keep_blank_chars=False) or "" 
            linhas_pagina = texto_pagina.split('\n')

            for linha in linhas_pagina:
                linha_norm = normalize_string(linha)
                if not linha_norm: 
                    continue

                if linha_norm in topicos_normalizados:
                    secao_atual = topicos_normalizados[linha_norm]
                    print(f"        -- Encontrado Tópico/Seção: '{secao_atual}'")
                    if secao_atual in topicos_importantes:
                        capturando = True
                        if secao_atual not in conteudo_extraido: 
                           conteudo_extraido[secao_atual] = ""

                        if secao_atual[0].isdigit() or secao_atual.startswith("ANEXO") or secao_atual == "IDENTIFICAÇÃO DO CURSO":
                           topico_pai_atual = secao_atual
                    else:
                        capturando = False
                        topico_pai_atual = None
                    continue 

                match_subtopico = re.match(r'^(\d+(\.\d+)+)\s+(.*)', linha_norm)
                if match_subtopico and topico_pai_atual and topico_pai_atual[0].isdigit(): 
                    prefixo_num = match_subtopico.group(1)
                    texto_subtopico = match_subtopico.group(3)
                    prefixo_pai = topico_pai_atual.split('.')[0]

                    if prefixo_num.startswith(prefixo_pai + "."):
                        if capturando and topico_pai_atual in conteudo_extraido:
                           conteudo_extraido[topico_pai_atual] += "\n" + linha.strip() + "\n"
                           print(f"          -- Adicionando subtópico '{prefixo_num}' ao pai '{topico_pai_atual}'")
                        continue 

                if capturando and secao_atual and secao_atual in conteudo_extraido:
                    conteudo_extraido[secao_atual] += linha.strip() + "\n" 

    for secao in conteudo_extraido:
         conteudo_extraido[secao] = '\n'.join(line for line in conteudo_extraido[secao].split('\n') if line.strip()) 
         conteudo_extraido[secao] = normalize_string(conteudo_extraido[secao].replace('\n', ' ')) 

    return conteudo_extraido

def extrair_chunks_de_texto(pdf_path):
    print("-> Executando: extrair_chunks_de_texto...")

    if not os.path.exists(pdf_path):
        print(f"    -- Erro: O arquivo '{pdf_path}' não foi encontrado.")
        return []

    conteudo_texto_puro = extrair_texto_corrido_por_topicos(pdf_path)
    conteudo_pagina_29 = tratar_pagina_29_excecao(pdf_path)

    for secao in conteudo_pagina_29:
        conteudo_pagina_29[secao] = normalize_string(conteudo_pagina_29[secao].replace('\n', ' '))

    conteudo_texto_puro.update(conteudo_pagina_29)

    dados_extraidos = []
    for secao, texto in conteudo_texto_puro.items():
        if texto:
            dados_extraidos.append({
                'tipo_info': 'texto_corrido',
                'secao': secao,
                'texto_bruto': texto
            })
        else:
            print(f"    -- AVISO: Seção '{secao}' extraída sem texto. Ignorando.")


    print(f"    -- Extração de Texto Corrido concluída: {len(dados_extraidos)} seções encontradas.")
    return dados_extraidos
