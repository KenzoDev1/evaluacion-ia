"""
Módulo de Seguridad — security_skill
Implementa validación de inputs, manejo seguro de credenciales
y rate limiting para proteger el agente contra abusos y fugas de datos.
"""

import os
import re
import time
from collections import deque

# ── Rate Limiting ──────────────────────────────────────────────────
# Cola de timestamps de ejecuciones recientes (máximo 10 por ventana de 60s)
_execution_timestamps: deque = deque()
RATE_LIMIT_MAX = 10
RATE_LIMIT_WINDOW_SECONDS = 60


def check_api_key() -> bool:
    """
    Verifica que GOOGLE_API_KEY exista en las variables de entorno.
    Si no existe, lanza ValueError antes de que el agente intente ejecutarse.
    El valor de la clave NUNCA se imprime ni se registra en logs.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or not api_key.strip():
        raise ValueError(
            "Error de Seguridad: GOOGLE_API_KEY no encontrada en el entorno. "
            "Verifica que el archivo .env exista y contenga la clave."
        )
    return True


def validate_input(user_input: str) -> str:
    """
    Valida y sanitiza el input del usuario aplicando tres capas de defensa:
    1. Rechazo de inputs vacíos o demasiado cortos (< 10 caracteres).
    2. Detección de patrones de inyección de prompt conocidos.
    3. Sanitización de caracteres potencialmente peligrosos.

    Retorna el input sanitizado si pasa todas las validaciones.
    """
    # Capa 1: Validación de longitud mínima
    stripped = user_input.strip() if user_input else ""
    if not stripped:
        raise ValueError("Error de Seguridad: El input no puede estar vacío.")

    if len(stripped) < 10:
        raise ValueError(
            "Error de Seguridad: El input es demasiado corto para constituir "
            "un reporte de incidente válido (mínimo 10 caracteres)."
        )

    # Capa 2: Detección de patrones de inyección de prompt
    suspicious_patterns = [
        r"ignora\s+(todas\s+)?las\s+instrucciones",
        r"ignore\s+(all\s+)?(previous\s+)?instructions",
        r"system\s*prompt",
        r"bypass",
        r"olvida\s+(las\s+)?instrucciones",
        r"eres\s+libre",
        r"desactiva\s+(tus\s+)?restricciones",
        r"act\s+as\s+if",
        r"pretend\s+you\s+are",
        r"reveal\s+(your\s+)?(system|instructions)",
    ]

    lower_input = stripped.lower()
    for pattern in suspicious_patterns:
        if re.search(pattern, lower_input):
            raise ValueError(
                "Error de Seguridad: Patrón sospechoso detectado en el input. "
                "Posible intento de inyección de prompt rechazado."
            )

    # Capa 3: Sanitización de caracteres HTML/script
    sanitized = stripped.replace("<", "&lt;").replace(">", "&gt;")
    sanitized = sanitized.replace("{{", "").replace("}}", "")

    return sanitized


def rate_limit() -> None:
    """
    Aplica rate limiting basado en ventana deslizante.
    Permite un máximo de 10 ejecuciones por ventana de 60 segundos.
    Si se excede, lanza PermissionError bloqueando la ejecución.
    """
    now = time.time()

    # Purgar timestamps fuera de la ventana
    while _execution_timestamps and (now - _execution_timestamps[0]) > RATE_LIMIT_WINDOW_SECONDS:
        _execution_timestamps.popleft()

    if len(_execution_timestamps) >= RATE_LIMIT_MAX:
        raise PermissionError(
            "Error de Seguridad: Rate limit excedido. "
            f"Máximo {RATE_LIMIT_MAX} ejecuciones por minuto. "
            "Espere antes de enviar otro incidente."
        )

    _execution_timestamps.append(now)
