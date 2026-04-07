# Asistente RAG - Prevención de Riesgos AquaChile

Este proyecto implementa un agente conversacional basado en RAG para consultar normativas de seguridad industrial.

## Requisitos
- Python 3.9+
- pip install langchain langchain-openai langchain-community chromadb pypdf

## Instrucciones de Ejecución
1. Clonar el repositorio.
2. Colocar un archivo PDF llamado `reglamento_seguridad.pdf` en la raíz del proyecto.
3. Insertar una API Key válida de OpenAI en el archivo `app.py`.
4. Ejecutar el script: `python app.py`