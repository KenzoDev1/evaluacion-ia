# Asistente RAG - Prevención de Riesgos AquaChile

Este proyecto implementa un agente conversacional basado en RAG para consultar normativas de seguridad industrial.

# Asistente de Prevención de Riesgos - AquaChile (Pipeline RAG)

Este proyecto implementa un agente conversacional basado en un pipeline RAG (Retrieval-Augmented Generation) para consultar normativas del Reglamento Interno de Higiene y Seguridad de AquaChile. El sistema restringe el conocimiento del modelo al documento oficial, evitando alucinaciones y garantizando trazabilidad.

## Requisitos Previos
Para ejecutar este proyecto, necesitas tener instalado Python 3.9 o superior.

## Instalación de Dependencias
1. Clona este repositorio o descarga los archivos en una carpeta local.
2. Abre una terminal en la ruta de la carpeta.
3. Instala las librerías necesarias ejecutando el siguiente comando:
   ```bash
   pip install python-dotenv langchain langchain-community langchain-google-genai langchain-text-splitters chromadb pypdf