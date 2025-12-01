
import re
import os
import json
from collections import defaultdict
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1300, chunk_overlap=230)

def gerar_chunks_matriz_curricular(itens_matriz):
    print("\n-> Gerando Chunks para Matriz Curricular (Detalhe + Sumário + MESTRE)...")
    chunks_matriz = []
    
    codigo_para_nome = {dado.get('codigo'): dado.get('nome') for dado in itens_matriz if dado.get('codigo') and dado.get('nome')}
    semestres_map = defaultdict(list)
    
    todas_disciplinas_ordenadas = []

    for dado in itens_matriz:
        if dado.get('semestre') and dado.get('nome'):
            semestres_map[dado.get('semestre')].append(dado.get('nome'))

    print("   -- Gerando Chunks de Detalhe...")
    for dado in itens_matriz:
        
        try:
            pre_req_codigos = dado.get('pre_requisitos', "Nenhum")
            pre_req_codigos = pre_req_codigos if pre_req_codigos and pre_req_codigos.strip() != '-' else "Nenhum"
            pre_req_texto = "não possui pré-requisitos"
            if pre_req_codigos != "Nenhum":
                codigos = re.findall(r'[A-Z]\d+', pre_req_codigos)
                nomes_pre_req = [f"'{codigo_para_nome.get(c)}'" for c in codigos if codigo_para_nome.get(c)]
                if nomes_pre_req:
                    pre_req_texto = f"seus pré-requisitos são: {', '.join(nomes_pre_req)}"
                else:
                    pre_req_texto = f"seus pré-requisitos são: {pre_req_codigos}"
            
            page_content = (
                f"A disciplina '{dado.get('nome', '?')}' (código {dado.get('codigo', '?')}) pertence ao {dado.get('semestre', '?')}º semestre do curso. "
                f"Ela tem uma carga horária de {dado.get('carga_horaria', '?')} horas, distribuídas em {dado.get('creditos_teoricos', '?')} créditos teóricos e "
                f"{dado.get('creditos_praticos', '?')} créditos práticos. Sobre os pré-requisitos, {pre_req_texto}."
            )
            metadata = {"fonte": "PPC - Tabela 9.6", "tipo": "disciplina_detalhe", "semestre": dado.get('semestre'), "nome_disciplina": dado.get('nome')}
            chunks_matriz.append({"page_content": page_content, "metadata": metadata})
        except Exception as e:
            print(f"   -- ERRO: {e}")

    print("   -- Gerando Chunks de Sumário por Semestre...")
    for semestre in sorted(semestres_map.keys()):
        try:
            nomes_disciplinas = semestres_map[semestre]
            todas_disciplinas_ordenadas.extend([f"{n} ({semestre}º Sem)" for n in nomes_disciplinas])
            
            nomes_str = ", ".join([f"'{n}'" for n in nomes_disciplinas])
            page_content = f"As disciplinas do {semestre}º semestre são: {nomes_str}."
            metadata = {"fonte": "PPC - Tabela 9.6", "tipo": "disciplina_sumario_semestre", "semestre": semestre}
            chunks_matriz.append({"page_content": page_content, "metadata": metadata})
        except Exception as e:
            print(f"   -- ERRO: {e}")

    print("   -- Gerando Chunk MESTRE (Todas as Disciplinas)...")
    try:
        lista_completa_str = "; ".join(todas_disciplinas_ordenadas)
        
        page_content = (
            f"RESUMO GERAL DA MATRIZ CURRICULAR. GRADE CURRICULAR COMPLETA. "
            f"LISTA DE TODAS AS DISCIPLINAS OBRIGATÓRIAS. QUAIS SÃO AS MATÉRIAS.\n"
            f"Abaixo segue a relação completa de todos os componentes curriculares e disciplinas "
            f"obrigatórias do curso de Sistemas de Informação, organizadas por semestre:\n"
            f"{lista_completa_str}."
        )
        
        metadata = {
            "fonte": "PPC - Matriz Curricular Completa",
            "tipo": "lista_completa_disciplinas", 
            "conteudo": "todas_disciplinas_obrigatorias_grade_materias"
        }
        
        chunks_matriz.append({"page_content": page_content, "metadata": metadata})
        print("   -- Chunk Mestre criado com sucesso!")
        
    except Exception as e:
        print(f"   -- ERRO ao criar Chunk Mestre: {e}")

    return chunks_matriz


def gerar_chunks_optativa_detalhe(itens_optativas):
  
    print("\n-> Gerando Chunks para Optativas (Detalhe)...")
    chunks_optativas = []
    
    for dado in itens_optativas:
        try:
            pre_req_texto = f"seu pré-requisito é: {dado.get('pre_requisitos', 'Nenhum')}"
            if dado.get('pre_requisitos') == "Nenhum" or not dado.get('pre_requisitos'):
                pre_req_texto = "não possui pré-requisitos"

            page_content = f"A disciplina optativa '{dado['nome']}' pertence ao {dado['grupo']}. Sua carga horária é de {dado['carga_horaria']} horas, com {dado['creditos_teoricos']} créditos teóricos e {dado['creditos_praticos']} créditos práticos. Para cursá-la, {pre_req_texto}."

            metadata = {"fonte": "PPC - Tabela 9.7 e 9.8",
                        "tipo": "disciplina_optativa",
                        "grupo": dado.get('grupo'),
                        "nome_disciplina": dado.get('nome')}
            chunks_optativas.append({"page_content": page_content, "metadata": metadata})
        except KeyError as e:
            print(f"   -- ERRO (Detalhe Optativa): Chave {e} faltando. Pulando item: {dado}")
        except Exception as e:
             print(f"   -- ERRO (Detalhe Optativa): Falha ao processar {dado.get('nome')}: {e}")
             
    print(f"   -- {len(chunks_optativas)} Chunks de Detalhe de Optativa criados.")
    return chunks_optativas

def gerar_chunks_optativa_resumo(itens_resumo):

    print("\n-> Gerando Chunks para Optativas (Resumo)...")
    chunks_resumo = []
    
    for dado in itens_resumo:
        try:
            nomes_lista = dado.get('nomes_disciplinas', [])
            if not nomes_lista: continue
            
            nomes_string = ", ".join([f"'{n}'" for n in nomes_lista])
            grupo = dado.get('grupo', 'Desconhecido')
            
            page_content = f"A lista completa de disciplinas optativas do {grupo} é: {nomes_string}."
            metadata = {"fonte": f"PPC - Tabela 9.7 e 9.8 (Resumo)",
                        "tipo": "resumo_grupo_optativas", # Nome de tipo mais específico
                        "grupo": grupo
                       }
            chunks_resumo.append({"page_content": page_content, "metadata": metadata})
        except Exception as e:
            print(f"   -- ERRO (Resumo Optativa): Falha ao processar resumo do {dado.get('grupo')}: {e}")

    print(f"   -- {len(chunks_resumo)} Chunks de Resumo de Optativa criados.")
    return chunks_resumo

def gerar_chunks_ementario(itens_ementario):
  
    print("\n-> Gerando Chunks para Ementário (Granular)...")
    chunks_ementario = []
    
    for dado in itens_ementario:
        try:
            disciplina = dado.get('disciplina', 'Disciplina não especificada')
            
            # Chunk 1: Ementa
            if dado.get('ementa'):
                chunks_ementario.append({
                    "page_content": f"A ementa da disciplina '{disciplina}' é: {dado['ementa']}", 
                    "metadata": {"fonte": "PPC - Ementário", "tipo": "ementa", "disciplina": disciplina}
                })
            
            if dado.get('objetivo'):
                chunks_ementario.append({
                    "page_content": f"O objetivo da disciplina '{disciplina}' é: {dado['objetivo']}", 
                    "metadata": {"fonte": "PPC - Ementário", "tipo": "objetivo_disciplina", "disciplina": disciplina}
                })
            
            if dado.get('bibliografia_basica'):
                chunks_ementario.append({
                    "page_content": f"A bibliografia básica para a disciplina '{disciplina}' é: {'; '.join(dado['bibliografia_basica'])}.", 
                    "metadata": {"fonte": "PPC - Ementário", "tipo": "bibliografia_basica", "disciplina": disciplina}
                })
                
            if dado.get('bibliografia_complementar'):
                chunks_ementario.append({
                    "page_content": f"A bibliografia complementar para a disciplina '{disciplina}' é: {'; '.join(dado['bibliografia_complementar'])}.", 
                    "metadata": {"fonte": "PPC - Ementário", "tipo": "bibliografia_complementar", "disciplina": disciplina}
                })
            
            page_content = f"Detalhes da disciplina '{disciplina}': Créditos: {dado.get('creditos', 'N/A')}, Carga Horária: {dado.get('carga_horaria', 'N/A')}, Departamento: {dado.get('departamento', 'N/A')}, Pré-requisito(s): {dado.get('pre_requisitos', 'Nenhum')}."
            chunks_ementario.append({
                "page_content": page_content, 
                "metadata": {"fonte": "PPC - Ementário", "tipo": "detalhes_disciplina", "disciplina": disciplina}
            })
        
        except KeyError as e:
            print(f"   -- ERRO (Ementário): Chave {e} não encontrada. Pulando item: {dado.get('disciplina')}")
        except Exception as e:
             print(f"   -- ERRO (Ementário): Falha ao processar {dado.get('disciplina')}: {e}")

    print(f"   -- {len(chunks_ementario)} Chunks granulares de Ementário criados.")
    return chunks_ementario


def gerar_chunks_atividades_comp(itens_atividades):
 
    print("\n-> Gerando Chunks para Atividades Complementares (Detalhe)...")
    chunks_detalhe = []
    
    for dado in itens_atividades:
        try:
            grupo_correto = dado.get('grupo', 'Grupo Não Associado') 
            item_num = dado.get('item')
            atividade = dado.get('atividade', 'atividade não especificada')
            carga_horaria = dado.get('carga_horaria', 'não especificada')
            ch_maxima = dado.get('ch_maxima', 'não especificada')
            
            item_str = f" (Item {item_num.strip()})" if item_num and item_num.strip() else ""

            page_content = (f"Na categoria de atividades complementares '{grupo_correto}', "
                            f"a atividade{item_str}: '{atividade}' possui uma carga horária de '{carga_horaria}' "
                            f"e um limite máximo de aproveitamento de {ch_maxima}.")

            metadata = {"fonte": "PPC - Atividades Complementares - Quadro 1",
                        "tipo": "atividade_complementar_detalhe",
                        "grupo": grupo_correto, 
                        "item": item_num,
                        "atividade": atividade}

            chunks_detalhe.append({"page_content": page_content, "metadata": metadata})
        except Exception as e:
             print(f"   -- ERRO (Atv Comp Detalhe): Falha ao processar {dado.get('atividade')}: {e}")
             
    print(f"   -- {len(chunks_detalhe)} Chunks de Detalhe de Atividades Comp. criados.")
    return chunks_detalhe

def gerar_chunks_atividades_resumo(itens_resumo):
    
    print("\n-> Gerando Chunks para Atividades Complementares (Resumo)...")
    chunks_resumo = []
    
    for dado in itens_resumo:
        try:
            chunks_resumo.append({
                "page_content": dado.get('page_content'),
                "metadata": dado.get('metadata')
            })
        except Exception as e:
             print(f"   -- ERRO (Atv Comp Resumo): Falha ao processar {dado.get('grupo')}: {e}")

    print(f"   -- {len(chunks_resumo)} Chunks de Resumo de Atividades Comp. criados.")
    return chunks_resumo

def gerar_chunks_equivalencia_obrigatoria(itens_equivalencia):

    print("\n-> Gerando Chunks para Equivalência de Obrigatórias...")
    chunks_equivalencia = []
    
    for dado in itens_equivalencia:
        try:
            base_info = f"Referente ao {dado['periodo']}, a disciplina \"{dado['disciplina_2012']}\" do PPC 2012 era de natureza {dado['nat_2012']} com carga horária de {dado['ch_2012']} horas."
            aproveitamento = dado['aproveitamento_2023']

            if not aproveitamento or aproveitamento[0]['disciplina'] in ('- - -', ''):
                page_content = base_info + " Ela não possui uma disciplina diretamente equivalente listada na matriz do PPC 2023."
            elif len(aproveitamento) == 1:
                nova = aproveitamento[0]
                page_content = f"{base_info} No PPC 2023, sua equivalência é a disciplina \"{nova['disciplina']}\", com carga horária de {nova['ch']} horas e natureza {nova['nat']}."
            else:
                page_content = base_info + " No PPC 2023, ela foi desmembrada ou é equivalente às seguintes disciplinas: " + ", ".join([f"\"{nova['disciplina']}\" (Carga Horária: {nova['ch']}h, Natureza: {nova['nat']})" for nova in aproveitamento]) + "."
            
            metadata = {"fonte": "PPC - Matriz de Equivalência", "tipo": "equivalencia_obrigatoria", "disciplina_2012": dado.get('disciplina_2012')}
            chunks_equivalencia.append({"page_content": page_content, "metadata": metadata})
        
        except KeyError as e:
            print(f"   -- ERRO (Equiv Obrigatória): Chave {e} faltando. Pulando item: {dado.get('disciplina_2012')}")
        except Exception as e:
            print(f"   -- ERRO (Equiv Obrigatória): Falha ao processar {dado.get('disciplina_2012')}: {e}")
            
    print(f"   -- {len(chunks_equivalencia)} Chunks de Equivalência Obrigatória criados.")
    return chunks_equivalencia

def gerar_chunks_equivalencia_optativa(itens_equivalencia_opt):
  
    print("\n-> Gerando Chunks para Equivalência de Optativas...")
    chunks_equivalencia_opt = []
    
    for dado in itens_equivalencia_opt:
        try:
            base_info = f"Do {dado['grupo']}, a disciplina optativa \"{dado['disciplina_2012']}\" do PPC 2012 tinha carga horária de {dado['ch_2012']} horas e natureza {dado['nat_2012']}."

            if dado.get('disciplina_2023'):
                page_content = f"{base_info} No PPC 2023, sua equivalência é a disciplina \"{dado['disciplina_2023']}\", com carga horária de {dado['ch_2023']} horas e natureza {dado['nat_2023']}."
            else:
                page_content = base_info + " Ela não possui uma equivalência direta listada para o PPC 2023."
            
            metadata = {"fonte": "PPC - Equivalência de Optativas", "tipo": "equivalencia_optativa", "disciplina_2012": dado.get('disciplina_2012')}
            chunks_equivalencia_opt.append({"page_content": page_content, "metadata": metadata})
        
        except KeyError as e:
            print(f"   -- ERRO (Equiv Optativa): Chave {e} faltando. Pulando item: {dado.get('disciplina_2012')}")
        except Exception as e:
            print(f"   -- ERRO (Equiv Optativa): Falha ao processar {dado.get('disciplina_2012')}: {e}")
            
    print(f"   -- {len(chunks_equivalencia_opt)} Chunks de Equivalência Optativa criados.")
    return chunks_equivalencia_opt

def gerar_chunks_corpo_docente_resumo(itens_resumo_docente):
   
    print("\n-> Gerando Chunks para Corpo Docente (Resumo)...")
    chunks_resumo_docente = []
    
    for dado in itens_resumo_docente:
        try:
            nomes_professores = dado.get('nomes', [])
            titulo_tabela = dado.get('titulo_tabela', 'Corpo Docente')
            
            if nomes_professores:
                page_content = (
                    f"O corpo docente do DComp ({titulo_tabela}) que atua no curso de "
                    f"Sistemas de Informação inclui: {', '.join(nomes_professores)}. "
                    f"Para detalhes sobre titulação, categoria ou regime de trabalho, "
                    f"pergunte sobre um professor específico."
                )
                metadata = {
                    "fonte": "PPC - Quadro 19.1",
                    "tipo": "corpo_docente_lista"
                }
                chunks_resumo_docente.append({"page_content": page_content, "metadata": metadata})
        except Exception as e:
             print(f"   -- ERRO (Resumo Docente): Falha ao processar resumo: {e}")
             
    print(f"   -- {len(chunks_resumo_docente)} Chunks de Resumo de Docentes criados.")
    return chunks_resumo_docente

def gerar_chunks_corpo_docente_individual(itens_docentes):
 
    print("\n-> Gerando Chunks para Corpo Docente (Detalhe)...")
    chunks_detalhe_docente = []
    
    for dado in itens_docentes:
        try:
            nome = dado.get('nome', 'N/A')
            if nome == 'N/A': continue # Pula se não tiver nome

            titulacao = dado.get('titulacao', 'N/A')
            cat_sigla = dado.get('categoria_sigla', 'N/A')
            cat_full = dado.get('categoria_full', cat_sigla)
            reg_sigla = dado.get('regime_sigla', 'N/A')
            reg_full = dado.get('regime_full', reg_sigla)

            page_content = (
                f"Docente do DComp (Departamento de Computação): {nome}. "
                f"Titulação: {titulacao}. "
                f"Categoria: {cat_sigla}"
                f"{f' ({cat_full})' if cat_sigla != cat_full else ''}. "
                f"Regime de Trabalho: {reg_sigla}"
                f"{f' ({reg_full})' if reg_sigla != reg_full else ''}."
            )
            metadata = {
                "fonte": "PPC - Quadro 19.1",
                "tipo": "corpo_docente_detalhe",
                "nome_professor": nome
            }
            chunks_detalhe_docente.append({"page_content": page_content, "metadata": metadata})
        except Exception as e:
             print(f"   -- ERRO (Detalhe Docente): Falha ao processar {dado.get('nome')}: {e}")

    print(f"   -- {len(chunks_detalhe_docente)} Chunks de Detalhe de Docentes criados.")
    return chunks_detalhe_docente

def gerar_chunks_texto_corrido(itens_texto_corrido):
    
    print("\n-> Gerando Chunks para Texto Corrido (Splitter)...")
    chunks_texto = []
    
    for dado in itens_texto_corrido:
        try:
            doc = Document(
                page_content=dado['texto_bruto'],
                metadata={"fonte": "PPC 2023", "secao": dado['secao']} # Metadata base
            )
            docs_divididos = text_splitter.split_documents([doc])
            
            for doc_chunk in docs_divididos:
                chunks_texto.append({
                    "page_content": doc_chunk.page_content,
                    "metadata": doc_chunk.metadata
                })
        except Exception as e:
             print(f"   -- ERRO (Texto Corrido): Falha ao dividir a seção {dado.get('secao')}: {e}")

    print(f"   -- {len(chunks_texto)} Chunks de Texto Corrido criados.")
    return chunks_texto


def gerar_chunks(lista_de_dados_unificada):
    
    print("\n-> Iniciando Geração de Chunks (Modo Despachante)...")
    chunks_finais = []
    
    dados_por_tipo = defaultdict(list)
    if not isinstance(lista_de_dados_unificada, list):
          print("Erro: Entrada principal não é uma lista.")
          return []
          
    for dado in lista_de_dados_unificada:
        if isinstance(dado, dict) and 'tipo_info' in dado:
            dados_por_tipo[dado['tipo_info']].append(dado)
        else:
            print(f"   -- AVISO: Item de dado inválido ou sem 'tipo_info': {dado}")
            
    print(f"   -- Dados separados por tipo: {list(dados_por_tipo.keys())}")

    if 'matriz_curricular' in dados_por_tipo:
        itens_matriz = dados_por_tipo['matriz_curricular']
        chunks_finais.extend(gerar_chunks_matriz_curricular(itens_matriz))
        
    if 'disciplina_optativa' in dados_por_tipo: 
        itens_optativas = dados_por_tipo['disciplina_optativa']
        chunks_finais.extend(gerar_chunks_optativa_detalhe(itens_optativas))

    if 'resumo_grupo' in dados_por_tipo:
        itens_resumo = dados_por_tipo['resumo_grupo']
        chunks_finais.extend(gerar_chunks_optativa_resumo(itens_resumo))

    if 'ementario' in dados_por_tipo:
        itens_ementario = dados_por_tipo['ementario']
        chunks_finais.extend(gerar_chunks_ementario(itens_ementario))

    if 'atividades_complementares' in dados_por_tipo:
        itens_atividades = dados_por_tipo['atividades_complementares']
        chunks_finais.extend(gerar_chunks_atividades_comp(itens_atividades))
        
    if 'resumo_categoria_atividades' in dados_por_tipo:
        itens_resumo_atv = dados_por_tipo['resumo_categoria_atividades']
        chunks_finais.extend(gerar_chunks_atividades_resumo(itens_resumo_atv))

    if 'equivalencia_obrigatoria' in dados_por_tipo:
        chunks_finais.extend(gerar_chunks_equivalencia_obrigatoria(dados_por_tipo['equivalencia_obrigatoria']))

    if 'equivalencia_optativa' in dados_por_tipo:
        chunks_finais.extend(gerar_chunks_equivalencia_optativa(dados_por_tipo['equivalencia_optativa']))

    if 'corpo_docente_resumo' in dados_por_tipo:
        chunks_finais.extend(gerar_chunks_corpo_docente_resumo(dados_por_tipo['corpo_docente_resumo']))

    if 'corpo_docente_individual' in dados_por_tipo:
        chunks_finais.extend(gerar_chunks_corpo_docente_individual(dados_por_tipo['corpo_docente_individual']))

    if 'texto_corrido' in dados_por_tipo:
        chunks_finais.extend(gerar_chunks_texto_corrido(dados_por_tipo['texto_corrido']))
        
    print(f"\n-> Geração de Chunks CONCLUÍDA. Total geral: {len(chunks_finais)} chunks.")
    return chunks_finais