# Informe Técnico: Implementación de Agente Funcional Autónomo para Auditoría de Riesgos Corporativos

**Evaluación Parcial N°2 - ISY0101**
**Institución:** DuocUC
**Autor:** Carlos Ignacio Bittner Navea

---

## 1. Introducción y Objetivo Organizacional

La integración de herramientas basadas en Inteligencia Artificial Generativa representa un cambio de paradigma en la administración de riesgos y la auditoría interna. El presente informe detalla la arquitectura y el diseño técnico de un **Agente Funcional Autónomo** desarrollado para la empresa AquaChile. 

El objetivo principal de este sistema es automatizar la recepción de reportes de incidentes (tanto operativos como de seguridad de la información), analizarlos de manera autónoma contrastándolos con las normativas corporativas vigentes, y emitir de forma estandarizada un acta de auditoría con la categorización del riesgo. Al minimizar el tiempo que transcurre entre el reporte de un incidente y la estructuración del acta resolutiva, AquaChile puede acelerar la activación de protocolos de contingencia, maximizando la continuidad del negocio y resguardando la integridad de sus colaboradores.

---

## 2. Justificación de Componentes Tecnológicos

Para cumplir con los estrictos requisitos de desacoplamiento, trazabilidad y precisión, se ha empleado una arquitectura modular. La orquestación y la lógica de negocio se encuentran completamente separadas (principio de responsabilidad única), delegando el comportamiento cognitivo a un orquestador LangChain.

### 2.1. Framework de Orquestación: LangChain
LangChain trasciende las capacidades de un modelo de lenguaje convencional permitiendo la creación de *Agentes*. La elección de este framework, y en particular el uso de `create_tool_calling_agent` y `AgentExecutor`, responde a tres necesidades críticas:
- **Modularidad Interna:** El archivo principal (`app.py`) contiene las herramientas y su lógica estructurada. El orquestador actúa como el director de orquesta que las invoca.
- **Flujos Secuenciales Restrictivos:** A través del `SystemMessage`, LangChain garantiza que el agente no altere el orden lógico de una auditoría: 1) Recopilar leyes, 2) Evaluar el nivel de riesgo, 3) Emitir y firmar el acta. 
- **Escalabilidad:** Si AquaChile decidiera integrar SAP, enviar notificaciones por Slack o consultar bases SQL corporativas, solo se requeriría añadir nuevas funciones con el decorador `@tool` dentro del mismo `app.py` y actualizar la lista de herramientas disponibles.

### 2.2. Motor de Inferencia: Google Gemini (gemini-2.5-flash)
Gemini fue seleccionado como el *cerebro* del agente por su alta eficiencia en razonamiento estructurado y su compatibilidad nativa con la invocación de herramientas (Tool Calling). El modelo `gemini-2.5-flash` ofrece un balance ideal entre velocidad de respuesta para aplicaciones de consola (CLI) y ventana de contexto extendida, siendo capaz de ingerir docenas de párrafos de reglamentación legal sin comprometer la velocidad de inferencia de la clasificación del riesgo.

### 2.3. Sistema de Recuperación Vectorial (Vector Store): ChromaDB
Para que el agente pueda sustentar sus decisiones en regulaciones empresariales y normativas estándar, es mandatorio un mecanismo de recuperación semántica. Se integró ChromaDB utilizando embeddings de Google (`gemini-embedding-001`) con una recuperación configurada a `k=12` fragmentos.
- **Precisión (Grounding):** Las alucinaciones (generación de hechos ficticios por el LLM) son inaceptables en una auditoría de riesgos. ChromaDB garantiza que la base del razonamiento del Agente provenga de la base documental previamente curada, y no del conocimiento general de internet del modelo.

---

## 3. Memoria y Contexto en el Sistema

El manejo del contexto en la Inteligencia Artificial moderna opera en dos dimensiones temporales, y el presente agente explota ambas para brindar una experiencia de auditoría conversacional profunda.

### 3.1. Memoria a Corto Plazo (Contexto de Sesión)
Se implementó `ConversationBufferMemory` a nivel de LangChain para retener el historial inmediato dentro de una sesión de terminal en curso. Si un operador reporta un incidente, el agente emite su conclusión. Si posteriormente el operador agrega: *"Añade al reporte que el supervisor no estaba presente"*, el Agente no inicia desde cero; comprende a qué reporte se refiere y procede a invocar nuevamente la herramienta de redacción (`redactar_acta_auditoria`) con el contenido anterior más la nueva condición. Esto emula la atención continua de un asesor humano.

### 3.2. Memoria a Largo Plazo (Recuperación Semántica)
A diferencia de la memoria conversacional que se borra al cerrar el script, ChromaDB funge como la memoria a largo plazo (permanente y estática) de la organización. Alberga toda la reglamentación. Cada vez que la herramienta `consultar_normativas_aquachile` es llamada, traduce la petición del usuario a un vector numérico (embedding) y recupera matemáticamente los artículos exactos de la norma que aplican, logrando que el agente actúe como un especialista que conoce cada inciso del manual.

---

## 4. Adaptabilidad y Toma de Decisiones (Casos de Uso)

El poder de un "Agente Funcional" reside en su planeación adaptativa frente a inputs no estructurados. 

### Caso de Uso A: Evento Catastrófico con Riesgo ISO 27001
**Situación reportada por el usuario:** *"Un servidor del centro de datos presentó sobrecalentamiento extremo originando humo en el cuarto de racks. El sistema contra incendios arrojó químicos sobre los servidores causando una caída masiva y hay exposición de bases de datos de empleados."*

**Proceso de decisión adaptativo del Agente:**
1. Al recibir la consulta, invoca `consultar_normativas_aquachile` buscando normativas sobre fuego en centro de datos e ISO 27001.
2. Trasladará la consulta a la función `evaluar_nivel_riesgo`. La función detectará palabras clave como "humo" (incendio), "químico" y "exposición de bases de datos" (brecha de datos). 
3. El sistema devolverá un **Nivel de Riesgo ALTO**. La justificación enfatizará el peligro tanto físico como la vulneración crítica a la integridad de la información (ISO 27001), priorizando planes de continuidad de negocio y mitigación.
4. El agente, entendiendo la gravedad, redactará un acta ejecutiva solicitando mitigación urgente antes de grabar en `acta_auditoria.txt`.

### Caso de Uso B: Condición Subestándar Leve
**Situación reportada por el usuario:** *"El empleado de la oficina 415 resbaló con el piso mojado cerca de la cafetería, sufrió una luxación de tobillo."*

**Proceso de decisión adaptativo del Agente:**
1. El Agente recuperará normativas relativas a limpieza, áreas comunes y prevención de accidentes menores.
2. La herramienta de riesgo evaluará las palabras ("resbaló", "luxación") y evitará falsos positivos. Aunque hubo lesión, no hay amenaza inminente a la vida o al negocio global. Clasificará el riesgo como **MEDIO**.
3. El acta resultante será redactada no como una emergencia de evacuación corporativa, sino recomendando la implementación de controles físicos preventivos (señalética de piso mojado) y seguimiento médico del trabajador, demostrando un discernimiento ajustado a la magnitud del evento.

---

## 5. Referencias Bibliográficas

- **Buitrago, C., & Sánchez, L.** (2022). *Sistemas de Gestión de Seguridad de la Información (ISO/IEC 27001) y su impacto en la prevención de riesgos organizacionales*. Revista Iberoamericana de Seguridad Informática.
- **Chroma Inc.** (2024). *Chroma Documentation: Embeddings and Vector Search*. Recuperado de https://docs.trychroma.com/
- **Google Cloud.** (2024). *Gemini API: Function Calling and Agent Orchestration*. Google for Developers. Recuperado de https://ai.google.dev/docs/function_calling
- **LangChain.** (2024). *Agents, Tools and Memory Management*. Documentación oficial de LangChain. Recuperado de https://python.langchain.com/docs/modules/agents/
