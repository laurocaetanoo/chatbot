
import pdfplumber
import re
import os
from collections import defaultdict

def parse_text_block(text):
    nat_regex = r'\b(OPT\s*-\s*G[\w\d-]+|OBR)\b'
    ch_regex = r'\b(60)\b'

    nat_match = re.search(nat_regex, text, re.IGNORECASE)
    ch_match = re.search(ch_regex, text)

    nat = nat_match.group(0).strip() if nat_match else None
    ch = ch_match.group(0) if ch_match else None

    name = text
    if ch: name = re.sub(ch_regex, '', name)
    if nat: name = re.sub(nat_regex, '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s+', ' ', name).strip()
    
    return name, ch, nat

def extrair_equivalencia_optativas(pdf_path: str):
    print("-> Executando: extrair_equivalencia_optativas...")
    
    paginas_alvo = [122, 123] 
    all_items = []
    current_group = "Não especificado"
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num in paginas_alvo:
                if page_num >= len(pdf.pages): continue
                page = pdf.pages[page_num]
                
                words = page.extract_words(x_tolerance=2, y_tolerance=2, keep_blank_chars=False)
                lines = defaultdict(list)
                for word in words: lines[round(word['top'], 0)].append(word)
                
                for y_pos in sorted(lines.keys()):
                    line_words = sorted(lines[y_pos], key=lambda w: w['x0'])
                    full_line_text = ' '.join(w['text'] for w in line_words)
                    
                    if full_line_text.lower().startswith('optativas - grupo'):
                        current_group = full_line_text
                        continue
                        
                    midpoint = page.width / 2
                    left_text = ' '.join(w['text'] for w in line_words if w['x0'] < midpoint)
                    right_text = ' '.join(w['text'] for w in line_words if w['x0'] > midpoint)
                    
                    name_2012, ch_2012, nat_2012 = parse_text_block(left_text)
                    name_2023, ch_2023, nat_2023 = parse_text_block(right_text)
                    
                    if ch_2012 and nat_2012:
                        all_items.append({'grupo': current_group, 'disciplina_2012': name_2012, 'ch_2012': ch_2012, 'nat_2012': nat_2012, 'disciplina_2023': name_2023, 'ch_2023': ch_2023, 'nat_2023': nat_2023})
                    elif (name_2012 or name_2023) and all_items:
                        last_item = all_items[-1]
                        if name_2012: last_item['disciplina_2012'] += ' ' + name_2012
                        if name_2023: last_item['disciplina_2023'] += ' ' + name_2023
    except Exception as e:
        print(f"   -- Erro ao processar PDF na extração de equivalência optativas: {e}")
        return []
    
    final_data_bruta = []
    for item in all_items:
        item['disciplina_2012'] = item['disciplina_2012'].strip()
        item['disciplina_2023'] = item['disciplina_2023'].strip() if item['disciplina_2023'] else ''
        item['tipo_info'] = 'equivalencia_optativa' 
        final_data_bruta.append(item)
    
    print(f"   -- Extração de Equivalência (Optativas) concluída: {len(final_data_bruta)} registros.")
    return final_data_bruta