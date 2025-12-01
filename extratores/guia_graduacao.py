
import re
import os
import json
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document 

def clean_text(text: str) -> str:
    text = re.sub(r'-\s*\n', '', text)
    text = re.sub(r'\s*\n\s*', ' ', text)
    text = re.sub(r'\s{2,}', ' ', text)
    patterns_to_remove = [
        r'Informações\s+[A-ZÇÃÉÍÓÚÊÂ]+\b',
        r'Conheça a página da biblioteca[^\n]*',
        r'Leia a Resolução nº[^\n]*',
        r'IFMA[^\n]*Página\s*\d+',
        r'http\S+',
    ]
    for pattern in patterns_to_remove:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    lines = [ln.strip() for ln in text.splitlines() if len(ln.strip()) > 20]
    text = ' '.join(lines)
    return text.strip()

def extrair_chunks_guia_graduacao(pdf_path):
    print(f"-> Executando: extrair_chunks_guia_graduacao ({pdf_path})...")
    
    if not os.path.exists(pdf_path):
        print(f"   -- Erro: O arquivo '{pdf_path}' não foi encontrado.")
        return []

    START_PAGE = 14
    IGNORE_PAGES = [22, 23, 24, 25, 26, 29, 30, 31, 35, 10]
    MIN_CHARS = 50
    PAGES_UNICOS = [7]

    try:
        print(f"   -- Carregando PDF via PyMuPDFLoader...")
        loader = PyMuPDFLoader(pdf_path)
        docs = loader.load()
        print(f"   -- Total de páginas extraídas: {len(docs)}")

        chunks_unicos = []
        for p in PAGES_UNICOS:
            doc = docs[p - 1]
            texto_pagina = doc.page_content.strip()
            chunks_unicos.append({
                "page_content": texto_pagina,
                "metadata": {
                    "source": pdf_path,
                    "secao": f"Página Especial {p}",
                    "page": p,
                }
            })
        print(f"   -- Páginas especiais (chunks únicos) extraídas.")

        all_text = []
        docs_com_pagina = [] 
        for i, doc in enumerate(docs, start=1):
            if i < START_PAGE or i in IGNORE_PAGES or i in PAGES_UNICOS:
                continue
            text = clean_text(doc.page_content)
            if len(text) > MIN_CHARS:
                docs_com_pagina.append(Document(page_content=text, metadata={"source": pdf_path, "page": i}))
        
        print(f"   -- {len(docs_com_pagina)} páginas de texto corrido serão processadas.")

        block_pattern = re.compile(
            r'(?=\b(?:O SUAP|E-mail Acadêmico @acad.ifma.edu.br|Caracterização Socioeconômica|'
            r'Carteira Estudantil SUAP|CARTEIRA DE MEIA|Wi-Fi|'
            r'Para efetivação da matrícula em disciplina isolada|A rematrícula é o ato|Alteração de Matrícula|Processo Eletrônico|O trancamento de matrícula|Reabertura de|'
            r'A transferência externa é|A transferência Interna ocorre|Desligamento|Trabalho de Conclusão|'
            r'Para solicitar o aproveitamento de disciplina|A disciplina de férias|O exercício domiciliar|'
            r'É considerado aprovado em cada|O estágio curricular é|A monitoria é|Colação de Grau|Para solicitar a emissão do diploma|'
            r'Nada Consta do DERI|Nada Consta da NAE|Biblioteca Marcelino Pacelli|O Enade|'
            r'Atividades Acadêmicas|Informações ACADÊMICAS)\b)'
        )
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=150,
            separators=["\n\n", "\n", ".", ";", " "]
        )
        
        final_chunks_texto_corrido = []
  
        for doc in docs_com_pagina:
            blocos_na_pagina = [b.strip() for b in re.split(block_pattern, doc.page_content) if len(b.strip()) > MIN_CHARS]
            
            for bloco in blocos_na_pagina:
                secao_preview = " ".join(bloco.split()[:7]) + "..."
                doc_bloco = Document(page_content=bloco, metadata=doc.metadata.copy())
                doc_bloco.metadata["secao"] = secao_preview 
                
                sub_chunks = splitter.split_documents([doc_bloco])
                
                for i, sub_chunk in enumerate(sub_chunks):
                    sub_chunk.metadata["chunk_id"] = f"page_{sub_chunk.metadata['page']}_block_{secao_preview[:20]}_{i}"
                    final_chunks_texto_corrido.append({
                        "page_content": sub_chunk.page_content,
                        "metadata": sub_chunk.metadata
                    })

        print(f"   -- {len(final_chunks_texto_corrido)} chunks de texto corrido criados.")
        
        chunks_finais_guia = final_chunks_texto_corrido + chunks_unicos
        print(f"   -- Extração do Guia concluída: {len(chunks_finais_guia)} chunks totais.")
        
        return chunks_finais_guia

    except Exception as e:
        print(f"   -- ERRO INESPERADO ao processar '{pdf_path}': {e}")
        return []