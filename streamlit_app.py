
import os
import streamlit as st
import re
import unicodedata
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

PASTA_INDICE_FAISS = "faiss_index"
MODELO_EMBEDDING_OPENAI = "text-embedding-3-small"
MODELO_LLM_RESPONDEDOR = "gemini-2.5-flash"
MODELO_LLM_LITE = "gemini-2.5-flash-lite" 

def aplicar_estilo_responsivo():
    st.markdown("""
        <style> 
                
        .stMarkdown p {
            font-size: 1.1rem; 
            line-height: 1.6;
        }
        
        @media (max-width: 768px) {
            
            h1 {
                font-size: 1.6rem !important;
            }
            
            .stMarkdown p {
                font-size: 0.90rem !important; 
                line-height: 1.5;
            }
            
            .stMarkdown li {
                font-size: 0.95rem !important;
            }

            .block-container {
                padding-top: 2rem !important;
                padding-left: 1rem !important;
                padding-right: 1rem !important;
                padding-bottom: 5rem !important;
            }
            
            .stChatInput textarea {
                font-size: 16px !important; 
            }
        }
        </style>
    """, unsafe_allow_html=True)



def carregar_api_keys():
    try:
        openai_key = st.secrets["OPENAI_API_KEY"]
        google_key = st.secrets["GOOGLE_API_KEY"]
        os.environ["OPENAI_API_KEY"] = openai_key
        os.environ["GOOGLE_API_KEY"] = google_key
        print("API Keys carregadas do Streamlit Secrets.")
    except Exception:
        if os.path.exists(".env"):
            load_dotenv()
            print("API Keys carregadas do arquivo .env local.")
        
        OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
        GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
        
        if not OPENAI_API_KEY or not GOOGLE_API_KEY:
            st.error("Erro: API Keys não encontradas.")
            st.stop()

@st.cache_resource
def carregar_retriever():
    print("Inicializando embedding OpenAI...")
    try:
        embeddings = OpenAIEmbeddings(model=MODELO_EMBEDDING_OPENAI)
    except Exception as e:
        st.error(f"Erro ao inicializar OpenAIEmbeddings: {e}")
        return None
    print("Embedding OpenAI inicializado.")

    print(f"Carregando índice FAISS da pasta: '{PASTA_INDICE_FAISS}'...")
    if not os.path.exists(PASTA_INDICE_FAISS):
        st.error(f"Erro: Pasta do índice FAISS '{PASTA_INDICE_FAISS}' não encontrada.")
        return None
            
    try:
        db = FAISS.load_local(
            PASTA_INDICE_FAISS,
            embeddings,
            allow_dangerous_deserialization=True
        )
        print("Índice FAISS carregado com sucesso.")
        retriever = db.as_retriever(search_kwargs={"k": 5})
        return retriever
    except Exception as e:
        st.error(f"Erro fatal ao carregar o índice FAISS: {e}")
        return None

@st.cache_resource
def carregar_modelos_llm():

    try:
        llm_resp = ChatGoogleGenerativeAI(model=MODELO_LLM_RESPONDEDOR, temperature=0.1)
        llm_class = ChatGoogleGenerativeAI(model=MODELO_LLM_LITE, temperature=0.0)
        llm_multiquery = ChatGoogleGenerativeAI(model=MODELO_LLM_LITE, temperature=0.7)
        llm_chitchat = ChatGoogleGenerativeAI(model=MODELO_LLM_LITE, temperature=0.4)
        print("Modelos LLMs inicializados com sucesso.")

        return llm_resp, llm_class, llm_multiquery, llm_chitchat
    except Exception as e:
        st.error(f"Erro ao inicializar os LLMs do Google (Gemini): {e}")
        return None, None

@st.cache_resource
def criar_chains(_llm_class, _llm_multiquery, _llm_chitchat):

    classify_prompt = ChatPromptTemplate.from_template("""
Analise a pergunta do usuário e classifique-a:
1. 'academico': Sobre o curso, disciplinas, regras, TCC, estágio, horários, administrativo.
2. 'chitchat': Saudação, conversa fiada, perguntas pessoais sobre o bot.
Responda APENAS: 'academico' ou 'chitchat'.
Pergunta: {input}
""")
    classify_chain = classify_prompt | _llm_class | StrOutputParser()
    
    multiquery_prompt = ChatPromptTemplate.from_template("""
Você é um assistente de IA especializado em reformular perguntas para um sistema de busca acadêmico.
Sua tarefa é gerar 3 versões diferentes da pergunta do usuário para ajudar a encontrar a resposta correta nos documentos do IFMA.
Diretrizes:
1. Use sinônimos técnicos (ex: "jubilamento" -> "desligamento", "cancelamento").
2. Se a pergunta for sobre "quais disciplinas" ou "quais matérias", inclua variações como "qual a grade curricular completa" e "lista de componentes obrigatórios".
3. Separe as perguntas por novas linhas. Não numere.

Pergunta original: {input}
""")
    multiquery_chain = multiquery_prompt | _llm_multiquery | StrOutputParser()

    chitchat_prompt = ChatPromptTemplate.from_template("""
Você é o Assistente Acadêmico de Sistemas de Informação do IFMA. Responda breve e educadamente.
Mantenha um tom profissional, mas acolhedor.                                                       
Usuário: {input}
Resposta:
""")
    chitchat_chain = chitchat_prompt | _llm_chitchat | StrOutputParser() 
    
    return classify_chain, multiquery_chain, chitchat_chain

def normalizar(s):
    if not s: return ""
    s = str(s).lower().strip()
    s = unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('ASCII')
    s = re.sub(r'[^\w\s]', '', s)
    return s

st.set_page_config(page_title="Assistente SI - IFMA", page_icon="🤖")

aplicar_estilo_responsivo()

with st.sidebar:
    st.header("Configurações")
    if st.button("🗑️ Nova Conversa"):
        st.session_state.messages = [] 
        st.rerun() 
    
    st.markdown("---")
    st.markdown("**Sobre:**\nChatbot para tirar dúvidas acadêmicas.")

st.title("🤖 Assistente Virtual de Sistemas de Informação - IFMA")
st.caption("Pergunte sobre disciplinas, regras do curso, equivalências...")

carregar_api_keys()
retriever = carregar_retriever()
llm_resp, llm_class, llm_multiquery, llm_chitchat = carregar_modelos_llm()

if retriever and llm_resp and llm_class and llm_multiquery and llm_chitchat:
    
    classify_chain, multiquery_chain, chitchat_chain = criar_chains(llm_class, llm_multiquery, llm_chitchat)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt_pergunta := st.chat_input("Digite sua pergunta..."):
        
        st.session_state.messages.append({"role": "user", "content": prompt_pergunta})
        with st.chat_message("user"):
            st.markdown(prompt_pergunta)

        with st.chat_message("assistant"):
            with st.spinner("Assistente: Entendendo a pergunta..."):
                try:
                    topico_raw = classify_chain.invoke(prompt_pergunta)

                    topico = normalizar(topico_raw)
                    print(f"Log: Classificador bruto='{topico_raw}' | normalizado='{topico}'")

                    PALAVRAS_ACADEMICAS = [
                        "academico", "academica", "ppc", "documento",
                        "oficial", "curricular", "matriz", "disciplina", 
                        "curso", "regra", "horas", "optativa"
                    ]

                    eh_academico = any(p in topico for p in PALAVRAS_ACADEMICAS)

                    if not topico:
                        eh_academico = True
                        print("Log: Classificação vazia, assumindo Acadêmico por segurança.")

                    if eh_academico:
                        st.spinner("Assistente: *Consultando documentos oficiais...*")
                        
                        variacoes_str = multiquery_chain.invoke(prompt_pergunta)
                        lista_perguntas = [prompt_pergunta] + variacoes_str.strip().split('\n')
                        print(f"Log: Perguntas geradas: {lista_perguntas}") 
                    
                        todos_docs = []
                        for p in lista_perguntas:
                            if p.strip():
                                docs = retriever.invoke(p.strip())
                                todos_docs.extend(docs)
                    
                        docs_unicos = []
                        conteudos_vistos = set()
                        for doc in todos_docs:
                            if doc.page_content not in conteudos_vistos:
                                docs_unicos.append(doc)
                                conteudos_vistos.add(doc.page_content)
                    
                        if not docs_unicos:
                            resposta_final = "Desculpe, não encontrei nenhuma informação relevante nos documentos oficiais sobre esse assunto específico."
                            print("Log: Curto-circuito ativado (0 documentos encontrados).")
                   
                        else:
                            contexto = "\n\n".join([d.page_content for d in docs_unicos[:10]])

                            prompt_rag = f"""
Você é um assistente acadêmico especialista no curso de Sistemas de Informação do IFMA.
Responda à pergunta do aluno usando **exclusivamente** o contexto abaixo.

REGRAS IMPORTANTES:
1. **Interprete o Contexto:** O documento pode usar termos técnicos (ex: "Integralização" = tempo para se formar; "Desligamento" = Jubilamento). Faça essas conexões.
2. **Modalidade do Curso:** O curso de Sistemas de Informação é **PRESENCIAL**. Não existe disciplinas EAD.
3. **Honestidade:** Se a resposta não estiver no contexto, diga "Não encontrei essa informação específica nos documentos oficiais".
4. **Sintetize:** Junte informações de diferentes partes do contexto para dar uma resposta completa.

Contexto Recuperado:
{contexto}

Pergunta do Aluno:
{prompt_pergunta}

Resposta Completa e Prestativa:
"""
                            resposta_obj = llm_resp.invoke(prompt_rag)
                            if resposta_obj and hasattr(resposta_obj, 'content'):
                                resposta_final = resposta_obj.content
                            else:
                                resposta_final = "Desculpe, não consegui gerar uma resposta."
                    
                    else:
                        st.spinner("Assistente: Pensando...")
                        resposta_final = chitchat_chain.invoke(prompt_pergunta)
                    
                    st.markdown(resposta_final)
                    st.session_state.messages.append({"role": "assistant", "content": resposta_final})

                except Exception as e:
                    st.error(f"Ocorreu um erro ao gerar a resposta: {e}")
else:
    st.error("O chatbot não pôde ser inicializado.")