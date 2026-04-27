import os
import time
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

# Configuración de rutas y modelo de embeddings
CHROMA_PATH = "./chroma_db_seguridad"
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

# 2. Lógica de Persistencia y Procesamiento por Lotes
if os.path.exists(CHROMA_PATH):
    print("Cargando base de datos vectorial existente desde el disco...")
    vectorstore = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)
else:
    print("Iniciando lectura del documento completo. Esto tomará varios minutos...")
    # Cargar el PDF completo
    loader = PyPDFLoader("reglamento_seguridad.pdf")
    docs = loader.load()
    
    # 3. Fragmentación (Chunking) - Ajustado a 500 y 50 para coincidir con el informe Word
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    splits = text_splitter.split_documents(docs)
    
    print(f"Documento dividido en {len(splits)} fragmentos. Iniciando vectorización por lotes...")
    
    # Inicializar Chroma vacío indicando dónde se guardará
    vectorstore = Chroma(embedding_function=embeddings, persist_directory=CHROMA_PATH)
    
    # 4. Procesamiento por lotes (Batching) con manejo de errores (Resistente a caídas)
    tamano_lote = 15  
    
    for i in range(0, len(splits), tamano_lote):
        lote = splits[i : i + tamano_lote]
        
        exito = False
        intentos = 0
        
        while not exito and intentos < 3:
            try:
                # Intentamos guardar el lote
                vectorstore.add_documents(lote)
                exito = True # Si pasa esta línea, funcionó
            except Exception as e:
                intentos += 1
                print(f"\n[!] Falló el intento {intentos}/3.")
                print(f"[!] EL ERROR REAL ES: {e}")
                
                if intentos < 3:
                    print("Esperando 20 segundos antes del próximo intento...")
                    time.sleep(20)
                else:
                    print("\n[X] Demasiados intentos fallidos. Deteniendo el programa.")
                    exit() # Esto corta la ejecución para que no siga en bucle
        
        # Calcular y mostrar el progreso
        fragmentos_procesados = min(i + tamano_lote, len(splits))
        porcentaje = (fragmentos_procesados / len(splits)) * 100
        print(f"Progreso: {fragmentos_procesados}/{len(splits)} fragmentos procesados ({porcentaje:.1f}%)...")
        
        # Pausa de 5 segundos entre lotes para respetar límites gratuitos
        if fragmentos_procesados < len(splits):
            time.sleep(5) 
            
    print("\n¡Base de datos creada y guardada con éxito!")

# Configurar el recuperador (¡Ahora buscando 12 fragmentos en vez de 4!)
retriever = vectorstore.as_retriever(search_kwargs={"k": 12})

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
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

def format_docs(documentos):
    return "\n\n".join(doc.page_content for doc in documentos)

rag_chain = (
    {"context": retriever | format_docs, "input": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# 7. Prueba rápida en terminal
print("\n=== SISTEMA INICIADO ===")
pregunta = input("Haz una pregunta sobre los protocolos de seguridad de AquaChile: ")
print(f"Pregunta: {pregunta}")
respuesta = rag_chain.invoke(pregunta)
print("\n=== RESPUESTA DEL AGENTE ===")
print(respuesta)