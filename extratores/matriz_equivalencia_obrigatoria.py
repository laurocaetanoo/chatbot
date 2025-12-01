
import pdfplumber
import pandas
import re
import os

def extrair_equivalencia_obrigatorias(pdf_path: str):
    print("-> Executando: extrair_equivalencia_obrigatorias...")   
    paginas_alvo = [120, 121] 
    all_table_rows = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num in paginas_alvo:
                if page_num < len(pdf.pages):
                    page = pdf.pages[page_num]
                    table = page.extract_table(table_settings={"vertical_strategy": "text", "horizontal_strategy": "text"})
                    if table:
                        all_table_rows.extend(table)
    except Exception as e:
        print(f"   -- Erro ao ler PDF na extração de equivalência: {e}")
        return []

    rows_de_8_colunas = [row for row in all_table_rows if row and len(row) == 8]
    if not rows_de_8_colunas:
        print("   -- AVISO: Nenhuma linha encontrada para a Matriz de Equivalência (Obrigatórias).")
        return []

    headers_temp = [f'col_{i}' for i in range(8)]
    df_temp = pandas.DataFrame(rows_de_8_colunas, columns=headers_temp)
    for col in headers_temp:
        df_temp[col] = df_temp[col].str.replace('\n', ' ', regex=False)

    df_corrigido = pandas.DataFrame({
        'disciplina_2012': (df_temp['col_0'].fillna('') + ' ' + df_temp['col_1'].fillna('')).str.strip(),
        'ch_2012': df_temp['col_2'], 'nat_2012': df_temp['col_3'],
        'aproveitamento_2023': (df_temp['col_4'].fillna('') + ' ' + df_temp['col_5'].fillna('')).str.strip(),
        'ch_2023': df_temp['col_6'], 'nat_2023': df_temp['col_7']
    })
    
    merged_data = []
    current_period = "Não especificado"
    for _, row in df_corrigido.iterrows():
        disciplina_2012 = str(row.get('disciplina_2012', '')).strip()
        ch_2012_str = str(row.get('ch_2012', '')).strip()
        aproveitamento_2023 = str(row.get('aproveitamento_2023', '')).strip()
        is_full_row = False
        try:
            int(ch_2012_str); is_full_row = bool(disciplina_2012)
        except (ValueError, TypeError): is_full_row = False
        
        if 'Período' in disciplina_2012:
            current_period = disciplina_2012
            continue
        if is_full_row:
            new_item = row.to_dict(); new_item['periodo'] = current_period
            merged_data.append(new_item)
        elif (disciplina_2012 or aproveitamento_2023) and merged_data:
            last_item = merged_data[-1]
            if disciplina_2012: last_item['disciplina_2012'] += ' ' + disciplina_2012
            if aproveitamento_2023: last_item['aproveitamento_2023'] += ' ' + aproveitamento_2023
            if row.get('ch_2023'): last_item['ch_2023'] += ' ' + str(row.get('ch_2023'))
            if row.get('nat_2023'): last_item['nat_2023'] += ' ' + str(row.get('nat_2023'))

    final_data_bruta = []
    for item in merged_data:
        for key, value in item.items():
            if isinstance(value, str): item[key] = re.sub(r'\s+', ' ', value).strip()
        
        aproveitamento_raw = item['aproveitamento_2023']
        chs_2023_raw = str(item['ch_2023'])
        nats_2023_raw = str(item['nat_2023'])
        
        disciplinas_2023 = [d.strip() for d in re.split(r'\s{2,}|,\s|,', aproveitamento_raw) if d.strip() and d.lower() != 'none']
        chs_2023 = [ch.strip() for ch in re.split(r'\s+', chs_2023_raw) if ch.strip()]
        nats_2023 = [nat.strip() for nat in re.split(r'\s+', nats_2023_raw) if nat.strip()]
        
        aproveitamento_list = []
        for i, disc in enumerate(disciplinas_2023):
            aproveitamento_list.append({'disciplina': disc, 'ch': chs_2023[i] if i < len(chs_2023) else '', 'nat': nats_2023[i] if i < len(nats_2023) else ''})
        
        processed_item = {
            'tipo_info': 'equivalencia_obrigatoria', 
            'periodo': item['periodo'],
            'disciplina_2012': item['disciplina_2012'],
            'ch_2012': item['ch_2012'],
            'nat_2012': item['nat_2012'],
            'aproveitamento_2023': aproveitamento_list
        }
        final_data_bruta.append(processed_item)

    print(f"   -- Extração de Equivalência (Obrigatórias) concluída: {len(final_data_bruta)} registros.")
    return final_data_bruta