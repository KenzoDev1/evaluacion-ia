import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# 1. Cargar variables de entorno (busca la clave GOOGLE_API_KEY en tu .env)
load_dotenv()

# 2. Cargar el documento PDF de la ACHS
loader = PyPDFLoader("reglamento_seguridad.pdf")
docs = loader.load()

# 3. Fragmentación (Chunking)
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
splits = text_splitter.split_documents(docs)

# 4. Crear Base de Datos Vectorial (Usando el modelo actual de Gemini)
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
vectorstore = Chroma.from_documents(documents=splits, embedding=embeddings)
retriever = vectorstore.as_retriever()

# 5. Configurar el Prompt
system_prompt = (
    "Eres un auditor y experto en prevención de riesgos laborales de AquaChile. "
    "Tu única función es responder dudas basándote ESTRICTAMENTE en los fragmentos del contexto. "
    "Si no está, responde: 'Esa información no figura en los protocolos de seguridad vigentes proporcionados.'\n\n"
    "Contexto recuperado: {context}\n"
)
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}"),
])

# 6. Crear el pipeline RAG usando Gemini 1.5 Flash
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)

def format_docs(documentos):
    return "\n\n".join(doc.page_content for doc in documentos)

rag_chain = (
    {"context": retriever | format_docs, "input": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# 7. Prueba rápida en terminal
pregunta = "¿Qué hacer en caso de incendio?"
respuesta = rag_chain.invoke(pregunta)
print("\n=== RESPUESTA DEL AGENTE ===")
print(respuesta)