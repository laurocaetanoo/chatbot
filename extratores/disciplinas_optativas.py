import pdfplumber
import os

def desempilhar_linha_complexa(linha):

    colunas_divididas = [str(celula).split('\n') for celula in linha]

    num_linhas_por_coluna = [len(c) for c in colunas_divididas]
   
    empilhamento_real = (len(colunas_divididas) > 1 and
                         num_linhas_por_coluna[0] == num_linhas_por_coluna[1] and
                         num_linhas_por_coluna[0] > 1)

    disciplinas_desempilhadas = []

    if empilhamento_real:
        for i in range(num_linhas_por_coluna[0]):
            try:
                nova_linha = [coluna[i].strip() for coluna in colunas_divididas]
                disciplinas_desempilhadas.append([item for item in nova_linha if item and item.strip()])
            except IndexError:
                pass
    else:
        linha_concatenada = []
        for idx, coluna in enumerate(colunas_divididas):
            linha_concatenada.append(" ".join([c.strip() for c in coluna if c.strip()]))
        disciplinas_desempilhadas.append(linha_concatenada)

    return disciplinas_desempilhadas


def extrair_disciplinas_optativas(caminho_pdf):
    import pdfplumber, os

    print("-> Executando: extrair_disciplinas_optativas...")

    if not os.path.exists(caminho_pdf):
        print(f"   -- Erro: O arquivo '{caminho_pdf}' não foi encontrado.")
        return []

    tabela_grupo_1, tabela_grupo_2 = None, []

    MARCADOR_PAGINA = "Tabela 9.7: Disciplinas Optativas Grupo I"

    with pdfplumber.open(caminho_pdf) as pdf:
        for i, pagina in enumerate(pdf.pages):
            texto = pagina.extract_text(x_tolerance=2)
            if texto and MARCADOR_PAGINA in texto:
                print(f"   -- Tabelas de optativas encontradas na página {i + 1}.")
                tabelas = pagina.extract_tables()
                if tabelas and len(tabelas) >= 2:
                    tabela_grupo_1 = tabelas[0]
                    tabela_grupo_2 = tabelas[1]
                else:
                    tabela_grupo_1 = tabelas[0] if tabelas else None
                
                if i + 1 < len(pdf.pages):
                    prox = pdf.pages[i + 1]
                    tabelas_prox = prox.extract_tables()
                    if tabelas_prox:
                        tabela_grupo_2.extend(tabelas_prox[0])
                break

    if not tabela_grupo_1 or not tabela_grupo_2:
        print("   -- AVISO: Não foi possível encontrar ambas as tabelas 9.7 e 9.8.")
        return []

    dados_grupo_1 = []
    dados_grupo_2 = []

    for linha in tabela_grupo_1[1:]:
        try:
            dados = [item.strip() for item in linha if item and item.strip()]
            if len(dados) < 2: continue
            dados_grupo_1.append({
                "grupo": "Grupo I", "nome": dados[0],
                "creditos_teoricos": int(dados[1]) if dados[1].isdigit() else 0,
                "creditos_praticos": 0,
                "carga_horaria": 60,
                "pre_requisitos": dados[-1] if len(dados) > 2 else "Nenhum",
                "tipo_info": "disciplina_optativa" 
            })
        except Exception:
            pass

    for linha in tabela_grupo_2[1:]:
        linhas_para_processar = []
        if any('\n' in str(c) for c in linha):
            linhas_para_processar.extend(desempilhar_linha_complexa(linha))
        else:
            linhas_para_processar.append([i.strip() for i in linha if i and i.strip()])

        for dados in linhas_para_processar:
            try:
                if len(dados) < 2: continue
                nome_disciplina = dados[0]
                numeros = [int(x) for x in dados if x and x.strip().isdigit()]
                textos = [x for x in dados[1:] if x and not x.strip().isdigit()]

                dados_grupo_2.append({
                    "grupo": "Grupo II",
                    "nome": nome_disciplina,
                    "creditos_teoricos": numeros[0] if len(numeros) > 0 else 0,
                    "creditos_praticos": numeros[1] if len(numeros) > 1 else 0,
                    "carga_horaria": 60,
                    "pre_requisitos": max(textos, key=len) if textos else "Nenhum",
                    "tipo_info": "disciplina_optativa" 
                })
            except Exception:
                pass

    print("   -- Criando chunks de resumo...")
    lista_final_de_dados = []

    if dados_grupo_1:
        nomes_g1 = [d['nome'] for d in dados_grupo_1]
        lista_final_de_dados.append({
            "tipo_info": "resumo_grupo",
            "grupo": "Grupo I",
            "nomes_disciplinas": nomes_g1 
        })

    if dados_grupo_2:
        nomes_g2 = [d['nome'] for d in dados_grupo_2]
        lista_final_de_dados.append({
            "tipo_info": "resumo_grupo",
            "grupo": "Grupo II",
            "nomes_disciplinas": nomes_g2 
        })

    lista_final_de_dados.extend(dados_grupo_1)
    lista_final_de_dados.extend(dados_grupo_2)

    print(f"   -- Extração concluída: {len(lista_final_de_dados)} itens de dados criados (incluindo resumos).")
    return lista_final_de_dados