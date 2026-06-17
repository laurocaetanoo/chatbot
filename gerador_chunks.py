from collections import defaultdict
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
 
 
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=2000,        
    chunk_overlap=300,      
    separators=["\n\n", "\n", ". ", "? ", "! ", " ", ""],
)
 
def _meta(fonte, tipo, titulo=None, **extras):
    metadata = {"fonte": fonte, "tipo": tipo}
    if titulo is not None:
        metadata["titulo"] = titulo
    metadata.update(extras)
    return metadata
 
 
def _chunk(page_content, metadata):
    return {"page_content": page_content, "metadata": metadata}
 
 
def gerar_matriz_curricular(itens):
    chunks = []
    codigo_para_nome = {d.get("codigo"): d.get("nome") for d in itens if d.get("codigo")}
    por_semestre = defaultdict(list)
 
    for d in itens:
        codigos = (d.get("pre_requisitos") or "").strip()
        if codigos in ("", "-", "Nenhum"):
            pre_req_texto = "não possui pré-requisitos"
        else:
            nomes = [f"'{codigo_para_nome[c]}'" for c in __import__("re").findall(r"[A-Z]\d+", codigos)
                     if codigo_para_nome.get(c)]
            pre_req_texto = (f"seus pré-requisitos são: {', '.join(nomes)}" if nomes
                             else f"seus pré-requisitos são: {codigos}")
 
        page_content = (
            f"A disciplina '{d.get('nome')}' (código {d.get('codigo')}) pertence ao "
            f"{d.get('semestre')}º semestre do curso. Ela tem carga horária de "
            f"{d.get('carga_horaria')} horas, distribuídas em {d.get('creditos_teoricos')} "
            f"créditos teóricos e {d.get('creditos_praticos')} créditos práticos. "
            f"Sobre os pré-requisitos, {pre_req_texto}."
        )
        chunks.append(_chunk(page_content, _meta(
            "PPC - Tabela 9.6", "disciplina_detalhe", titulo=d.get("nome"),
            semestre=d.get("semestre"))))
        if d.get("semestre") and d.get("nome"):
            por_semestre[d["semestre"]].append(d["nome"])
 
    todas = []
    for semestre in sorted(por_semestre):
        nomes = por_semestre[semestre]
        todas.extend(f"{n} ({semestre}º Sem)" for n in nomes)
        nomes_str = ", ".join(f"'{n}'" for n in nomes)
        chunks.append(_chunk(
            f"As disciplinas do {semestre}º semestre são: {nomes_str}.",
            _meta("PPC - Tabela 9.6", "disciplina_sumario_semestre",
                  titulo=f"{semestre}º semestre", semestre=semestre)))
 
    if todas:
        page_content = (
            "RESUMO GERAL DA MATRIZ CURRICULAR. GRADE CURRICULAR COMPLETA. "
            "LISTA DE TODAS AS DISCIPLINAS OBRIGATÓRIAS. QUAIS SÃO AS MATÉRIAS. "
            "Abaixo segue a relação completa de todos os componentes curriculares "
            "obrigatórios do curso de Sistemas de Informação, organizados por semestre: "
            f"{'; '.join(todas)}."
        )
        chunks.append(_chunk(page_content, _meta(
            "PPC - Matriz Curricular Completa", "lista_completa_disciplinas",
            titulo="Grade curricular completa")))
    return chunks
 
 
def gerar_optativas(itens):
    chunks = []
    por_grupo = defaultdict(list)
 
    for d in itens:
        pre = d.get("pre_requisitos")
        pre_texto = ("não possui pré-requisitos" if not pre or pre == "Nenhum"
                     else f"seu pré-requisito é: {pre}")
        page_content = (
            f"A disciplina optativa '{d['nome']}' pertence ao {d['grupo']}. "
            f"Sua carga horária é de {d['carga_horaria']} horas, com "
            f"{d['creditos_teoricos']} créditos teóricos e {d['creditos_praticos']} "
            f"créditos práticos. Para cursá-la, {pre_texto}."
        )
        chunks.append(_chunk(page_content, _meta(
            "PPC - Tabela 9.7 e 9.8", "disciplina_optativa",
            titulo=d["nome"], grupo=d.get("grupo"))))
        por_grupo[d["grupo"]].append(d["nome"])
 
    for grupo, nomes in por_grupo.items():
        nomes_str = ", ".join(f"'{n}'" for n in nomes)
        chunks.append(_chunk(
            f"A lista completa de disciplinas optativas do {grupo} é: {nomes_str}.",
            _meta("PPC - Tabela 9.7 e 9.8 (Resumo)", "resumo_grupo_optativas",
                  titulo=f"Optativas do {grupo}", grupo=grupo)))
    return chunks
 
def gerar_ementario(itens):
    chunks = []
    for d in itens:
        disc = d.get("disciplina", "Disciplina não especificada")
        fonte = "PPC - Ementário"
 
        if d.get("ementa"):
            chunks.append(_chunk(f"A ementa da disciplina '{disc}' é: {d['ementa']}",
                                 _meta(fonte, "ementa", titulo=disc)))
        if d.get("objetivo"):
            chunks.append(_chunk(f"O objetivo da disciplina '{disc}' é: {d['objetivo']}",
                                 _meta(fonte, "objetivo_disciplina", titulo=disc)))
        if d.get("bibliografia_basica"):
            chunks.append(_chunk(
                f"A bibliografia básica para a disciplina '{disc}' é: "
                f"{'; '.join(d['bibliografia_basica'])}.",
                _meta(fonte, "bibliografia_basica", titulo=disc)))
        if d.get("bibliografia_complementar"):
            chunks.append(_chunk(
                f"A bibliografia complementar para a disciplina '{disc}' é: "
                f"{'; '.join(d['bibliografia_complementar'])}.",
                _meta(fonte, "bibliografia_complementar", titulo=disc)))
 
        chunks.append(_chunk(
            f"Detalhes da disciplina '{disc}': Créditos: {d.get('creditos', 'N/A')}, "
            f"Carga Horária: {d.get('carga_horaria', 'N/A')}, "
            f"Departamento: {d.get('departamento', 'N/A')}, "
            f"Pré-requisito(s): {d.get('pre_requisitos', 'Nenhum')}.",
            _meta(fonte, "detalhes_disciplina", titulo=disc)))
    return chunks
 
def gerar_atividades_complementares(itens):
    chunks = []
    por_categoria = defaultdict(list)
    fonte = "PPC - Atividades Complementares - Quadro 1"
 
    for d in itens:
        grupo = d.get("grupo", "Grupo Não Associado")
        item = (d.get("item") or "").strip()
        item_str = f" (Item {item})" if item else ""
        page_content = (
            f"Na categoria de atividades complementares '{grupo}', a atividade{item_str}: "
            f"'{d.get('atividade')}' possui carga horária de '{d.get('carga_horaria')}' "
            f"e limite máximo de aproveitamento de {d.get('ch_maxima')}."
        )
        chunks.append(_chunk(page_content, _meta(
            fonte, "atividade_complementar_detalhe", titulo=d.get("atividade"),
            grupo=grupo, item=d.get("item"))))
        por_categoria[grupo].append(d)
 
    for grupo, ativs in por_categoria.items():
        linhas = [f"{(a.get('item') or '').strip()}. {a.get('atividade')} "
                  f"(Máx.: {a.get('ch_maxima')})" for a in ativs]
        chunks.append(_chunk(
            f"A categoria de atividades complementares '{grupo}' inclui as seguintes "
            f"atividades: {'; '.join(linhas)}.",
            _meta(fonte, "resumo_categoria_atividades", titulo=grupo, grupo=grupo)))
 
    if itens:
        blocos = []
        for grupo, ativs in por_categoria.items():
            nomes = "; ".join(a.get("atividade", "") for a in ativs)
            blocos.append(f"Categoria '{grupo}': {nomes}")
        page_content = (
            "RESUMO GERAL DAS ATIVIDADES COMPLEMENTARES. TODAS AS ATIVIDADES "
            "COMPLEMENTARES DO CURSO. Abaixo, todas as atividades complementares "
            f"aceitas, organizadas por categoria. {'. '.join(blocos)}."
        )
        chunks.append(_chunk(page_content, _meta(
            fonte, "resumao_atividades", titulo="Todas as atividades complementares")))
    return chunks
 
 
def gerar_equivalencia_obrigatoria(itens):
    chunks = []
    for d in itens:
        base = (f"Referente ao {d['periodo']}, a disciplina \"{d['disciplina_2012']}\" do "
                f"PPC 2012 era de natureza {d['nat_2012']} com carga horária de "
                f"{d['ch_2012']} horas.")
        aprov = d.get("aproveitamento_2023") or []
        if not aprov:
            page_content = base + " Ela não possui equivalência direta na matriz do PPC 2023."
        elif len(aprov) == 1:
            n = aprov[0]
            page_content = (f"{base} No PPC 2023, sua equivalência é a disciplina "
                            f"\"{n['disciplina']}\", com carga horária de {n['ch']} horas "
                            f"e natureza {n['nat']}.")
        else:
            partes = ", ".join(f"\"{n['disciplina']}\" (CH: {n['ch']}h, Natureza: {n['nat']})"
                               for n in aprov)
            page_content = (base + " No PPC 2023, ela é equivalente às seguintes "
                            f"disciplinas: {partes}.")
        chunks.append(_chunk(page_content, _meta(
            "PPC - Matriz de Equivalência", "equivalencia_obrigatoria",
            titulo=d.get("disciplina_2012"), periodo=d.get("periodo"))))
    return chunks
 
 
def gerar_equivalencia_optativa(itens):
    chunks = []
    for d in itens:
        base = (f"Do {d['grupo']}, a disciplina optativa \"{d['disciplina_2012']}\" do "
                f"PPC 2012 tinha carga horária de {d['ch_2012']} horas e natureza "
                f"{d['nat_2012']}.")
        if d.get("disciplina_2023"):
            page_content = (f"{base} No PPC 2023, sua equivalência é a disciplina "
                            f"\"{d['disciplina_2023']}\", com carga horária de "
                            f"{d['ch_2023']} horas e natureza {d['nat_2023']}.")
        else:
            page_content = base + " Ela não possui equivalência direta no PPC 2023."
        chunks.append(_chunk(page_content, _meta(
            "PPC - Equivalência de Optativas", "equivalencia_optativa",
            titulo=d.get("disciplina_2012"), grupo=d.get("grupo"))))
    return chunks
 

TITULO_DOCENTES = "Quadro 19.1 - Docentes do DComp"
 
 
def gerar_corpo_docente(itens):
    chunks = []
    nomes = []
    fonte = "PPC - Quadro 19.1"
 
    for d in itens:
        nome = d.get("nome")
        if not nome:
            continue
        cat_sigla, cat_full = d.get("categoria_sigla", ""), d.get("categoria_full", "")
        reg_sigla, reg_full = d.get("regime_sigla", ""), d.get("regime_full", "")
        page_content = (
            f"Docente do DComp (Departamento de Computação): {nome}. "
            f"Titulação: {d.get('titulacao', 'N/A')}. "
            f"Categoria: {cat_sigla}{f' ({cat_full})' if cat_full and cat_full != cat_sigla else ''}. "
            f"Regime de Trabalho: {reg_sigla}{f' ({reg_full})' if reg_full and reg_full != reg_sigla else ''}."
        )
        chunks.append(_chunk(page_content, _meta(
            fonte, "corpo_docente_detalhe", titulo=nome)))
        nomes.append(nome)
 
    if nomes:
        page_content = (
            f"O corpo docente do DComp ({TITULO_DOCENTES}) que atua no curso de "
            f"Sistemas de Informação inclui: {', '.join(nomes)}. Para detalhes de "
            f"titulação, categoria ou regime, pergunte sobre um professor específico."
        )
        chunks.append(_chunk(page_content, _meta(
            fonte, "corpo_docente_lista", titulo="Lista de docentes do DComp")))
    return chunks
 
 
def gerar_texto_corrido(itens):
    chunks = []
    for d in itens:
        doc = Document(page_content=d["texto_bruto"],
                       metadata=_meta("PPC 2023", "texto_corrido",
                                      titulo=d.get("secao"), secao=d.get("secao")))
        for parte in text_splitter.split_documents([doc]):
            chunks.append(_chunk(parte.page_content, parte.metadata))
    return chunks
 
 
GERADORES = {
    "matriz_curricular": gerar_matriz_curricular,
    "disciplina_optativa": gerar_optativas,
    "ementario": gerar_ementario,
    "atividades_complementares": gerar_atividades_complementares,
    "equivalencia_obrigatoria": gerar_equivalencia_obrigatoria,
    "equivalencia_optativa": gerar_equivalencia_optativa,
    "corpo_docente_individual": gerar_corpo_docente,
    "texto_corrido": gerar_texto_corrido,
}
 
 
def gerar_chunks(lista_de_dados_unificada):
    print("\n-> Iniciando geração de chunks (despachante)")
    if not isinstance(lista_de_dados_unificada, list):
        print("[erro] Entrada não é uma lista.")
        return []
 
    por_tipo = defaultdict(list)
    for dado in lista_de_dados_unificada:
        if isinstance(dado, dict) and "tipo_info" in dado:
            por_tipo[dado["tipo_info"]].append(dado)
        else:
            print(f"Item inválido ou sem 'tipo_info': {dado}")
 
    chunks_finais = []
    for tipo, itens in por_tipo.items():
        gerador = GERADORES.get(tipo)
        if gerador is None:
            print(f"Sem gerador para o tipo_info '{tipo}' ({len(itens)} itens ignorados).")
            continue
        gerados = gerador(itens)
        print(f"   - {tipo}: {len(itens)} itens -> {len(gerados)} chunks")
        chunks_finais.extend(gerados)
 
    print(f"-> Geração concluída. Total: {len(chunks_finais)} chunks.")
    return chunks_finais