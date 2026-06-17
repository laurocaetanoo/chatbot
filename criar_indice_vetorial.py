import json
import os
import shutil
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
 
load_dotenv()
 
PASTA_INDICE_FAISS = "faiss_index"
MODELO_EMBEDDING_OPENAI = "text-embedding-3-small"
ARQUIVO_JSON_CHUNKS = "chunks_completos.json"
 
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
 
if not OPENAI_API_KEY:
    print("Erro: A chave OPENAI_API_KEY não foi encontrada no arquivo .env")
    exit()
    
print("API Key da OpenAI carregada com sucesso do arquivo .env.")
 
def carregar_chunks_do_json(caminho_json):
    print(f"Carregando chunks do arquivo: {caminho_json}...")
    with open(caminho_json, 'r', encoding='utf-8') as f:
        dados_chunks = json.load(f)
 
    documentos = []
    ignorados = 0
    for chunk in dados_chunks:
        if not isinstance(chunk, dict) or 'page_content' not in chunk or 'metadata' not in chunk:
            ignorados += 1
            continue
        documentos.append(Document(page_content=chunk['page_content'], metadata=chunk['metadata']))
 
    if ignorados:
        print(f"Aviso: {ignorados} chunk(s) malformado(s) ignorado(s) (sem 'page_content' ou 'metadata').")
    print(f"Total de {len(documentos)} documentos carregados.")
    return documentos
 
def criar_e_salvar_indice_faiss_openai(documentos, pasta_indice):
    
    if not documentos:
        print("Nenhum documento para indexar. Encerrando.")
        return
 
    print("Inicializando modelo de embedding da OpenAI (text-embedding-3-small)")
    try:
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        print("Modelo de embedding OpenAI inicializado.")
    except Exception as e:
        print(f"Erro ao inicializar OpenAIEmbeddings: {e}")
        return
 
    print("Criando o índice FAISS com embeddings da OpenAI")
    try:
        db = FAISS.from_documents(documentos, embeddings)
        print("Índice FAISS criado com sucesso.")
    except Exception as e:
        print(f"Erro ao criar o índice FAISS com OpenAI: {e}")
        return
 
    db.save_local(pasta_indice)
    print(f"Índice salvo localmente na pasta: '{pasta_indice}'")
    print(f"Total de vetores no índice: {db.index.ntotal} (esperado: {len(documentos)}).")
 
 
if __name__ == "__main__":
 
    if os.path.exists(PASTA_INDICE_FAISS):
        print(f"Removendo a pasta '{PASTA_INDICE_FAISS}' antiga...")
        shutil.rmtree(PASTA_INDICE_FAISS)
 
    documentos_para_indexar = carregar_chunks_do_json(ARQUIVO_JSON_CHUNKS)
 
    if documentos_para_indexar:
        criar_e_salvar_indice_faiss_openai(documentos_para_indexar, PASTA_INDICE_FAISS)
    else:
        print("Nenhum documento foi carregado.")
 
    print("\n--- PROCESSO DE CRIAÇÃO DO ÍNDICE COM OPENAI CONCLUÍDO ---")