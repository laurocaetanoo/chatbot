# 🤖 Chatbot Acadêmico SI - IFMA

Este repositório contém o desenvolvimento de um chatbot acadêmico baseado em arquitetura **RAG (Retrieval-Augmented Generation)**, criado para apoiar a resolução de dúvidas acadêmicas dos discentes do curso de **Sistemas de Informação do IFMA**.

O sistema foi desenvolvido como parte de um **Trabalho de Conclusão de Curso (TCC)** e utiliza documentos institucionais oficiais, como o **Projeto Pedagógico do Curso (PPC)** e o **Guia da Graduação**, para fornecer respostas mais contextualizadas, confiáveis e alinhadas às normas da instituição.

## 📌 Objetivo

O projeto tem como objetivo oferecer um canal de apoio informacional capaz de responder dúvidas acadêmicas relacionadas a temas como:

- matriz curricular;
- pré-requisitos de disciplinas;
- atividades complementares;
- Trabalho de Conclusão de Curso (TCC);
- matrícula e rematrícula;
- procedimentos e normas acadêmicas.

A proposta busca reduzir dificuldades de acesso à informação e tornar a consulta a documentos institucionais mais rápida, direta e acessível para os estudantes.

## 🧠 Arquitetura da solução

O sistema foi estruturado com base na arquitetura **RAG**, combinando:

1. **extração e preparação dos documentos institucionais**;
2. **geração de chunks textuais**;
3. **vetorização com embeddings**;
4. **armazenamento em índice vetorial FAISS**;
5. **recuperação de contexto relevante**;
6. **geração de resposta com modelo de linguagem**.

Além do fluxo RAG para perguntas acadêmicas, a aplicação também possui um fluxo simplificado para interações do tipo **chitchat**.

## 🛠️ Tecnologias utilizadas

- **Python**
- **Streamlit**
- **LangChain**
- **FAISS**
- **OpenAI Embeddings**
- **Google Gemini**
- **pdfplumber**
- **PyMuPDFLoader**

## 🧱 Estrutura do projeto

A organização do projeto contempla, entre outros, os seguintes componentes:

- scripts de extração dos dados brutos do PPC e do Guia da Graduação;
- módulo de geração e organização dos chunks;
- módulo de criação do índice vetorial;
- aplicação principal do chatbot em Streamlit.

🔐 Observações
O chatbot foi concebido para atuar sobre documentos institucionais oficiais do IFMA.
As respostas acadêmicas dependem da base documental processada e do índice vetorial gerado.
Este projeto possui finalidade acadêmica, no contexto de um Trabalho de Conclusão de Curso.
📚 Contexto acadêmico

Este projeto foi desenvolvido como Trabalho de Conclusão de Curso (TCC) com o tema:

Desenvolvimento de um Chatbot para Apoio à Resolução de Dúvidas Acadêmicas no Curso de Sistemas de Informação do IFMA

👨‍💻 Autor

Lauro Caetano Silva de Abreu
Graduando em Sistemas de Informação - IFMA
