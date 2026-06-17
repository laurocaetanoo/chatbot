import json
import os
from collections import Counter
 
from gerador_chunks import gerar_chunks
 
from extratores.matriz_curricular_obrigatoria import extrair_matriz_curricular
from extratores.disciplinas_optativas import extrair_disciplinas_optativas
from extratores.atv_complementares import extrair_atividades_complementares
from extratores.matriz_equivalencia_obrigatoria import extrair_equivalencia_obrigatorias
from extratores.matriz_equivalencia_optativas import extrair_equivalencia_optativas
from extratores.corpo_docente import extrair_dados_corpo_docente
from extratores.ementario import extrair_ementario
from extratores.textocorrido_ppc import extrair_texto_corrido
 
from extratores.guia_graduacao import extrair_chunks_guia_graduacao
 
 
NOME_ARQUIVO_PPC = "PPC 2023 - Sistemas de Informação.pdf"
NOME_ARQUIVO_GUIA = "Guia-da-Graduacao.pdf"
NOME_ARQUIVO_SAIDA = "chunks_completos.json"
 
EXTRATORES_PPC = [
    ("Matriz curricular", extrair_matriz_curricular),
    ("Optativas (9.7/9.8)", extrair_disciplinas_optativas),
    ("Atividades complementares", extrair_atividades_complementares),
    ("Equivalência obrigatórias", extrair_equivalencia_obrigatorias),
    ("Equivalência optativas", extrair_equivalencia_optativas),
    ("Corpo docente", extrair_dados_corpo_docente),
    ("Ementário", extrair_ementario),
    ("Texto corrido", extrair_texto_corrido),
]
 
 
def salvar_json(dados, caminho_arquivo):
    with open(caminho_arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)
    print(f"\nArquivo final '{caminho_arquivo}' salvo com sucesso!")
 
 
def coletar_dados_brutos_ppc(caminho_pdf):
    dados = []
    for nome, extrator in EXTRATORES_PPC:
        try:
            itens = extrator(caminho_pdf)
            print(f"   - {nome}: {len(itens)} registros")
            dados.extend(itens)
        except Exception as e:
            print(f"   - [ERRO] {nome} falhou: {e}")
    return dados
 
 
def resumir_por_tipo(itens, rotulo):
    print(f"\nResumo de {rotulo} por tipo:")
    contagem = Counter(
        d.get("tipo_info") if isinstance(d, dict) and "tipo_info" in d
        else (d.get("metadata", {}).get("tipo") if isinstance(d, dict) else "?")
        for d in itens
    )
    for tipo, n in sorted(contagem.items(), key=lambda x: str(x[0])):
        print(f"   {n:5d}  {tipo}")
 
 
def main():
    print("--- INICIANDO PROCESSAMENTO COMPLETO ---")
 
    if not os.path.exists(NOME_ARQUIVO_PPC):
        print(f"[erro] PDF do PPC não encontrado: '{NOME_ARQUIVO_PPC}'. "
              f".")
        return
 
    print("\n--- Pipeline 1: extraindo dados brutos do PPC... ---")
    dados_brutos = coletar_dados_brutos_ppc(NOME_ARQUIVO_PPC)
    print(f"-> {len(dados_brutos)} registros de dados brutos coletados.")
    resumir_por_tipo(dados_brutos, "dados brutos")
 
    chunks_pipeline_1 = gerar_chunks(dados_brutos)
 
    chunks_pipeline_2 = []
    if os.path.exists(NOME_ARQUIVO_GUIA):
        print("\n--- Pipeline 2: extraindo chunks do Guia da Graduação... ---")
        chunks_pipeline_2 = extrair_chunks_guia_graduacao(NOME_ARQUIVO_GUIA)
        print(f"-> {len(chunks_pipeline_2)} chunks do Guia coletados.")
    else:
        print(f"\n Guia não encontrado ('{NOME_ARQUIVO_GUIA}'); "
              f"Pipeline 2 ignorado.")
 
    print("\n-> Combinando todos os chunks...")
    chunks_finais = chunks_pipeline_1 + chunks_pipeline_2
    print(f"-> Total de {len(chunks_finais)} chunks finais.")
 
    if chunks_finais:
        resumir_por_tipo(chunks_finais, "chunks finais")
        salvar_json(chunks_finais, NOME_ARQUIVO_SAIDA)
    else:
        print("\nNenhum chunk foi gerado.")
 
    print("\n--- PROCESSAMENTO FINALIZADO ---")
 
 
if __name__ == "__main__":
    main()