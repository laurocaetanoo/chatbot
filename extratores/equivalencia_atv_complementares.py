
import pdfplumber
import re
import os
from collections import defaultdict # Importa o defaultdict aqui

TABLE_HEADER_KEYWORDS = ['Item', 'Atividades', 'Carga Horária (CH)', 'CH Máxima']
DEFAULT_GROUP_NAME = "Grupo Não Associado (Verificar PDF)"

SECTION_HEADERS_LIST = [
    "Atividades Acadêmico-Científico que incluem Ensino e Pesquisa",
    "Atividades de Extensão, Artístico-culturais e Esportivas",
    "Experiências Ligadas a Formação Profissional",
    "Produção Técnica ou Científica",
    "Atividades de Vivências de Gestão",
    "Atividades de Ação Social, Voluntariado e Filantropia"
]
SECTION_COUNTS = [8, 6, 6, 5, 2, 2] 

def clean_text(text):
    if text is None: return ""
    return re.sub(r'\s+', ' ', text.replace('\n', ' ')).strip()

def find_table_header_row_index(table_data, keywords):
    for i, row in enumerate(table_data):
        if row is None: continue
        try:
            row_items = [str(cell) if cell is not None else '' for cell in row]
            row_text = ' '.join(filter(None, row_items)).lower()
            if all(keyword.lower() in row_text for keyword in keywords):
                return i
        except Exception:
            continue
    return None

def roman_to_int(s):
    s = s.strip().upper()
    roman_map = {'I': 1, 'V': 5, 'X': 10}
    val = 0
    try:
        for i in range(len(s)):
            if i > 0 and roman_map[s[i]] > roman_map[s[i-1]]:
                val += roman_map[s[i]] - 2 * roman_map[s[i-1]]
            else:
                val += roman_map[s[i]]
        return val
    except KeyError:
        return 0

def _criar_dados_de_resumo_atividades(dados_atividades_corrigidos):
    print("   ... Fase 3: Criando dados de resumo por categoria...")
    
    if not dados_atividades_corrigidos:
        print("      ... Nenhuma atividade complementar encontrada para resumir.")
        return []

    grupos = defaultdict(list)
    for dado in dados_atividades_corrigidos:
        grupos[dado.get('grupo', DEFAULT_GROUP_NAME)].append(dado)

    lista_de_resumos = []
    count_resumos_criados = 0
    for grupo_nome, atividades_do_grupo in grupos.items():
        if grupo_nome == DEFAULT_GROUP_NAME: continue

        page_content_summary = f"A categoria de atividades complementares '{grupo_nome}' inclui as seguintes atividades:\n"
        
        try:
            atividades_do_grupo.sort(key=lambda x: roman_to_int(x.get('item', '')))
        except Exception as e:
            print(f"      Aviso: Falha ao ordenar itens para o grupo '{grupo_nome}'. Erro: {e}")

        lista_atividades_str = []
        for dado_ativ in atividades_do_grupo:
            item_str = f"Item {dado_ativ.get('item', '').strip()}:"
            ativ_str = dado_ativ.get('atividade', 'N/A')
            carga_str = dado_ativ.get('carga_horaria', 'N/A')
            max_str = dado_ativ.get('ch_maxima', 'N/A')
            lista_atividades_str.append(f"* {item_str} {ativ_str} (Carga: {carga_str} | Máximo: {max_str})")

        page_content_summary += "\n".join(lista_atividades_str)
        
        metadata_summary = {
            "fonte": "PPC - Atividades Complementares - Quadro 1 (Resumo)",
            "tipo": "resumo_categoria_atividades",
            "grupo": grupo_nome
        }
        
        dado_resumo = {
            'tipo_info': 'resumo_categoria_atividades',
            'page_content': page_content_summary,
            'metadata': metadata_summary
        }
        lista_de_resumos.append(dado_resumo)
        count_resumos_criados += 1

    print(f"   ... {count_resumos_criados} dados de resumo foram criados.")
    return lista_de_resumos

def extrair_atividades_complementares(caminho_pdf):
    print("-> Executando: extrair_atividades_complementares (v17 - Final)...")
    dados_extraidos = [] 
    pagina_inicial = 118
    pagina_final = 120

    if not os.path.exists(caminho_pdf):
        print(f"   -- Erro: O arquivo '{caminho_pdf}' não foi encontrado.")
        return []

    print("--- Fase 1: Extraindo linhas de dados (Lógica v15) ---")
    item_regex = re.compile(r'^(I|II|III|IV|V|VI|VII|VIII)[\s\.]?$', re.IGNORECASE) 

    with pdfplumber.open(caminho_pdf) as pdf:
        for i in range(pagina_inicial - 1, min(pagina_final, len(pdf.pages))):
            page = pdf.pages[i]
            page_num = i + 1
            print(f"   Processando Página {page_num}...")

            page_tables = page.find_tables()
            if not page_tables: continue

            for tbl_idx, table_obj in enumerate(page_tables):
                table_data = table_obj.extract()
                if not table_data: continue
                
                header_idx_tbl = find_table_header_row_index(table_data, TABLE_HEADER_KEYWORDS)
                if header_idx_tbl is None: continue 
                
                header_row = [clean_text(h) for h in table_data[header_idx_tbl]]
                col_map = {name: h_idx for h_idx, name in enumerate(header_row) if name}
                
                col_item = col_map.get('Item', -1)
                col_atividade = col_map.get('Atividades', -1)
                col_ch = col_map.get('Carga Horária (CH)', -1)
                col_ch_max = col_map.get('CH Máxima', -1)

                if col_atividade == -1 or col_item == -1: continue

                data_rows = table_data[header_idx_tbl + 1:]

                for row_idx, row in enumerate(data_rows):
                    if not row or not any(cell for cell in row if cell is not None): continue
                    
                    item_texto = clean_text(row[col_item]) if col_item < len(row) else ""
                    atividade_texto = clean_text(row[col_atividade]) if col_atividade < len(row) else ""
                    
                    if atividade_texto.lower() == 'atividades' or item_texto.lower() == 'item':
                        continue

                    if item_regex.match(item_texto):
                        carga_horaria_texto = clean_text(row[col_ch]) if col_ch != -1 and col_ch < len(row) else ""
                        ch_maxima_texto = clean_text(row[col_ch_max]) if col_ch_max != -1 and col_ch_max < len(row) else ""
                        
                        dados_extraidos.append({
                            'tipo_info': 'atividades_complementares',
                            'grupo': DEFAULT_GROUP_NAME,
                            'item': item_texto,
                            'atividade': atividade_texto,
                            'carga_horaria': carga_horaria_texto,
                            'ch_maxima': ch_maxima_texto
                        })
                    
                    elif len(dados_extraidos) > 0:
                        last_item = dados_extraidos[-1]
                        carga_horaria_texto = clean_text(row[col_ch]) if col_ch != -1 and col_ch < len(row) else ""
                        ch_maxima_texto = clean_text(row[col_ch_max]) if col_ch_max != -1 and col_ch_max < len(row) else ""

                        last_item['atividade'] += ' ' + item_texto
                        last_item['atividade'] += ' ' + atividade_texto
                        last_item['carga_horaria'] += ' ' + carga_horaria_texto
                        last_item['ch_maxima'] += ' ' + ch_maxima_texto
                        
                        last_item['atividade'] = clean_text(last_item['atividade'])
                        last_item['carga_horaria'] = clean_text(last_item['carga_horaria'])
                        last_item['ch_maxima'] = clean_text(last_item['ch_maxima'])
                    
    print(f"\n-> Extração (v15) concluída: {len(dados_extraidos)} atividades encontradas.")
    
    print("--- Fase 2: Atribuindo grupos por contagem fixa (v11) ---")
    
    total_esperado = sum(SECTION_COUNTS)
    if len(dados_extraidos) != total_esperado:
        print(f"   --- !!! ATENÇÃO !!! ---")
        print(f"   A extração encontrou {len(dados_extraidos)} atividades, mas esperávamos {total_esperado}.")
    else:
        print(f"   --- SUCESSO: Contagem de {len(dados_extraidos)} atividades corresponde ao esperado ({total_esperado}). ---")
    
    dados_corrigidos = [] 
    current_index = 0 
    
    for i, group_name in enumerate(SECTION_HEADERS_LIST):
        count = SECTION_COUNTS[i]
        print(f"   Atribuindo grupo '{group_name}' para os próximos {count} itens...")
        
        fatia_de_dados = dados_extraidos[current_index : current_index + count]
        
        for item_dado in fatia_de_dados:
            item_dado['grupo'] = group_name 
            dados_corrigidos.append(item_dado)
            
        current_index += count 
        
    if current_index < len(dados_extraidos):
        print(f"   Aviso: {len(dados_extraidos) - current_index} atividades extras foram encontradas. Atribuindo ao último grupo.")
        for item_dado in dados_extraidos[current_index:]:
            item_dado['grupo'] = SECTION_HEADERS_LIST[-1] 
            dados_corrigidos.append(item_dado)

    print("   Atribuição de grupos por contagem concluída.")
   
    lista_de_resumos = _criar_dados_de_resumo_atividades(dados_corrigidos)
    
    dados_corrigidos.extend(lista_de_resumos)
    
    print(f"\n-> Extração e Processamento (v17) concluídos: {len(dados_corrigidos)} dados totais gerados (Individuais + Resumos).")
 
    return dados_corrigidos