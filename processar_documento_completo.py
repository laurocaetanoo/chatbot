import json
import os
from collections import defaultdict 

from gerador_chunks import gerar_chunks
from extratores.matriz_curricular_obrigatoria import extrair_matriz_curricular
from extratores.disciplinas_optativas import extrair_disciplinas_optativas 
from extratores.equivalencia_atv_complementares import extrair_atividades_complementares 
from extratores.matriz_equivalencia_obrigatoria import extrair_equivalencia_obrigatorias 
from extratores.matriz_equivalencia_optativas import extrair_equivalencia_optativas
from extratores.ementario import extrair_ementario
from extratores.corpo_docente import extrair_dados_corpo_docente
from extratores.textosemtabela import extrair_chunks_de_texto

from extratores.guia_graduacao import extrair_chunks_guia_graduacao


def salvar_json(dados, caminho_arquivo):
    with open(caminho_arquivo, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)
    print(f"\nArquivo final '{caminho_arquivo}' salvo com sucesso!")

if __name__ == "__main__":
    
    NOME_ARQUIVO_PPC = 'PPC 2023 - Sistemas de Informação.pdf' 
    NOME_ARQUIVO_GUIA = 'Guia-da-Graduacao.pdf' 
    NOME_ARQUIVO_SAIDA = 'chunks_completos.json'

    print("--- INICIANDO PROCESSAMENTO COMPLETO DO PPC ---")

    print("\n--- Pipeline 1: Extraindo dados estruturados (Tabelas, Ementário)... ---")    
    dados_brutos_para_formatar = []
    
    print("Processando PPC (Tabelas)...")
    dados_brutos_para_formatar.extend(extrair_matriz_curricular(NOME_ARQUIVO_PPC))
    dados_brutos_para_formatar.extend(extrair_disciplinas_optativas(NOME_ARQUIVO_PPC))
    dados_brutos_para_formatar.extend(extrair_atividades_complementares(NOME_ARQUIVO_PPC))
    dados_brutos_para_formatar.extend(extrair_equivalencia_obrigatorias(NOME_ARQUIVO_PPC))
    dados_brutos_para_formatar.extend(extrair_equivalencia_optativas(NOME_ARQUIVO_PPC))
    dados_brutos_para_formatar.extend(extrair_dados_corpo_docente(NOME_ARQUIVO_PPC)) 
    dados_brutos_para_formatar.extend(extrair_ementario(NOME_ARQUIVO_PPC))
    dados_brutos_para_formatar.extend(extrair_chunks_de_texto(NOME_ARQUIVO_PPC))

    print(f"-> {len(dados_brutos_para_formatar)} registros de dados brutos coletados.")

    chunks_pipeline_1 = gerar_chunks(dados_brutos_para_formatar)
    
    print("\n--- Pipeline 2: Extraindo chunks pré-formatados (Guia da Graduação)... ---")
    chunks_pipeline_2 = []
    
    print("Processando Guia da Graduação (Texto Corrido)...")
    chunks_pipeline_2.extend(extrair_chunks_guia_graduacao(NOME_ARQUIVO_GUIA)) 
    
    print(f"-> {len(chunks_pipeline_2)} chunks de texto pré-formatados coletados.")

    print("\n-> Combinando todos os chunks...")
    chunks_finais = chunks_pipeline_1 + chunks_pipeline_2
    
    print(f"-> Total de {len(chunks_finais)} chunks finais gerados.")

    if chunks_finais:
        salvar_json(chunks_finais, NOME_ARQUIVO_SAIDA)
    else:
        print("\nNenhum chunk foi gerado.")
    
    print("\n--- PROCESSAMENTO FINALIZADO ---")