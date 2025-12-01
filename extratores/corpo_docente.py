
import pdfplumber
import re
import os

def extrair_dados_corpo_docente(pdf_path, page_num=79):
    
    print(f"-> Executando: extrair_dados_corpo_docente (Página {page_num})...")
    dados_extraidos_final = []
    page_index = page_num - 1 

    if not os.path.exists(pdf_path):
        print(f"  -- Erro: O arquivo '{pdf_path}' não foi encontrado.")
        return []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            if page_index >= len(pdf.pages):
                print(f"  -- Erro: Número de página {page_num} fora do intervalo.")
                return []

            page = pdf.pages[page_index]

            table_title = "Quadro 19.1 - Docentes do DComp"
            abbreviation_definitions = {
                "EBTT": "Ensino Básico e Técnico",
                "MS": "Magistério Superior",
                "DE": "Dedicação Exclusiva"
            }

            tables = page.extract_tables()
            if not tables:
                print(f"  -- Erro: Nenhuma tabela encontrada na página {page_num}.")
                return []

            professor_table = tables[0]

            if not professor_table or len(professor_table) < 2:
                 print(f"  -- Erro: Estrutura da tabela de professores inválida na página {page_num}.")
                 return []

            extracted_header = professor_table[0]
            data_rows = professor_table[1:]
            num_extracted_columns = len(extracted_header)
            print(f"  -- Info: Detectadas {num_extracted_columns} colunas no header: {extracted_header}")

            col_indices = {'name': 0, 'titulation': 1, 'category': 2, 'regime': 3}
            if num_extracted_columns < 4:
                 print(f"  -- Erro: Colunas essenciais parecem faltar. Não é possível processar.")
                 return []

            lista_professores_individuais = []
            professor_names_list = []

            for row in data_rows:
                if len(row) < 4:
                    print(f"  -- Aviso: Pulando linha com colunas insuficientes: {row}")
                    continue

                name = row[col_indices['name']].strip() if row[col_indices['name']] else "N/A"
                if name == "N/A":
                    print(f"  -- Aviso: Pulando linha com nome 'N/A': {row}")
                    continue 

                titulation = row[col_indices['titulation']].strip() if row[col_indices['titulation']] else "N/A"
                category_abbr = row[col_indices['category']].strip() if row[col_indices['category']] else "N/A"
                regime_abbr = row[col_indices['regime']].strip() if row[col_indices['regime']] else "N/A"

                name = name.replace('\n', ' ')
                titulation = titulation.replace('\n', ' ')

                category_full = abbreviation_definitions.get(category_abbr, category_abbr)
                regime_full = abbreviation_definitions.get(regime_abbr, regime_abbr)

                professor_data = {
                    'tipo_info': 'corpo_docente_individual',
                    'nome': name,
                    'titulacao': titulation,
                    'categoria_sigla': category_abbr,
                    'categoria_full': category_full,
                    'regime_sigla': regime_abbr,
                    'regime_full': regime_full
                }
                lista_professores_individuais.append(professor_data)
                professor_names_list.append(name) 

            if professor_names_list:
                resumo_data = {
                    'tipo_info': 'corpo_docente_resumo',
                    'titulo_tabela': table_title,
                    'nomes': professor_names_list
                }
                dados_extraidos_final.append(resumo_data)

            dados_extraidos_final.extend(lista_professores_individuais)

    except FileNotFoundError:
        print(f"  -- Erro: Arquivo PDF não encontrado em {pdf_path}")
    except Exception as e:
        print(f"  -- Erro inesperado durante extração da página {page_num}: {e}")

    print(f"  -- Extração Corpo Docente concluída: {len(dados_extraidos_final)} registros gerados (1 resumo + {len(lista_professores_individuais)} individuais).")
    return dados_extraidos_final

