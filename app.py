import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_classic.memory import ConversationBufferMemory

from langchain_core.tools import tool
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma

CHROMA_PATH = "./chroma_db_seguridad"

@tool
def consultar_normativas_aquachile(query: str) -> str:
    """
    Busca normativas y protocolos en la base vectorial de seguridad (ChromaDB) de AquaChile.
    Útil para consultar reglamentos y procedimientos aplicables a una situación o incidente.
    """
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
        if not os.path.exists(CHROMA_PATH):
            return "Error: La base de datos vectorial no existe en ./chroma_db_seguridad."
            
        vectorstore = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)
        retriever = vectorstore.as_retriever(search_kwargs={"k": 12})
        docs = retriever.invoke(query)
        
        if not docs:
            return "No se encontraron normativas relevantes en los protocolos de seguridad."
            
        return "\n\n".join(doc.page_content for doc in docs)
    except Exception as e:
        return f"Error al consultar el reglamento: {e}"

@tool
def evaluar_nivel_riesgo(descripcion: str) -> str:
    """
    Evalúa el nivel de riesgo de un incidente de seguridad (Alto, Medio, Bajo).
    La evaluación sigue los estándares de auditoría interna y normativas como ISO 27001.
    """
    desc = descripcion.lower()
    
    # Criterios estrictos alineados con prevención de riesgos laborales y seguridad de la información (ISO 27001)
    criterios_alto = ['fuego', 'incendio', 'explosión', 'muerte', 'amputación', 'derrame químico', 'químico', 'asfixia', 'electrocución', 'brecha de datos', 'fuga de información']
    criterios_medio = ['caída', 'resbaló', 'aceite', 'corte', 'sangre', 'fractura', 'golpe', 'luxación', 'acceso no autorizado']
    
    if any(keyword in desc for keyword in criterios_alto):
        riesgo = "ALTO"
        justificacion = "Situación crítica con potencial de peligro vital, daño estructural severo o vulneración grave a la seguridad operativa e integridad de la información. El evento demanda activación inmediata de protocolos de emergencia y mitigación extrema según estándares corporativos y normas como ISO 27001."
    elif any(keyword in desc for keyword in criterios_medio):
        riesgo = "MEDIO"
        justificacion = "Incidente que compromete la integridad física o seguridad del entorno, requiriendo atención médica o mitigación de controles físicos (ej. controles de acceso ISO 27001), pero sin representar un peligro de muerte inminente ni pérdida total de operaciones."
    else:
        riesgo = "BAJO"
        justificacion = "Evento aislado o condición subestándar menor que no representa un riesgo significativo de daño personal, material o a la continuidad del negocio."
        
    return f"CLASIFICACIÓN DE RIESGO: {riesgo}\nJUSTIFICACIÓN TÉCNICA: {justificacion}"

@tool
def redactar_acta_auditoria(conclusiones: str) -> str:
    """
    Toma las conclusiones finales de la auditoría y las guarda en un archivo de texto plano (acta_auditoria.txt).
    """
    filename = "acta_auditoria.txt"
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write("=== ACTA OFICIAL DE AUDITORÍA DE PREVENCIÓN DE RIESGOS ===\n\n")
            f.write(conclusiones)
            f.write("\n\n==========================================================\n")
        return f"Éxito: Acta de auditoría redactada y guardada correctamente en el archivo '{filename}'."
    except Exception as e:
        return f"Error al guardar el acta: {e}"

load_dotenv()

# Lista de herramientas disponibles para el agente
tools = [consultar_normativas_aquachile, evaluar_nivel_riesgo, redactar_acta_auditoria]

# Inicialización del modelo Gemini
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

system_prompt = """Eres un Auditor de Prevención de Riesgos de AquaChile.
Tu trabajo es procesar situaciones y redactar actas.

DEBES SEGUIR ESTRICTAMENTE ESTE ORDEN (NO TE SALTES NINGÚN PASO):
1. Primero, invoca 'consultar_normativas_aquachile' para recuperar de la base vectorial las normas que aplican al incidente descrito por el usuario.
2. Segundo, invoca 'evaluar_nivel_riesgo' usando la descripción del usuario para obtener una evaluación formal de riesgo basada en normativas estrictas.
3. Tercero, consolida toda la información recopilada e invoca 'redactar_acta_auditoria' para guardarla.

Indica siempre al usuario los hallazgos y confirma si el acta ha sido guardada en disco.
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(
    agent=agent, 
    tools=tools, 
    memory=memory, 
    verbose=True, 
    handle_parsing_errors=True
)

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🤖 SISTEMA AUTÓNOMO DE AUDITORÍA - AQUACHILE")
    print("="*60 + "\n")
    
    while True:
        try:
            user_input = input("\nDescriba el incidente a auditar (o escriba 'salir' para terminar):\n> ")
            if user_input.lower().strip() in ['salir', 'exit', 'quit']:
                print("\nCerrando el sistema. ¡Hasta luego!")
                break
                
            if not user_input.strip():
                continue
                
            print("\n[Procesando con el Agente LangChain...]\n")
            respuesta = agent_executor.invoke({"input": user_input})
            
            print("\n" + "="*60)
            print("✅ RESOLUCIÓN:")
            print("="*60)
            output = respuesta["output"]
            if isinstance(output, list):
                partes = []
                for item in output:
                    if isinstance(item, str):
                        partes.append(item)
                    elif isinstance(item, dict) and "text" in item:
                        partes.append(item["text"])
                output = " ".join(partes)
            print(output + "\n")
            
        except KeyboardInterrupt:
            print("\n\nCierre forzado.")
            break
        except Exception as e:
            print(f"\nError durante la ejecución: {e}\n")