"""
Módulo de Observabilidad — observability_skill
Instrumenta el agente LangChain capturando métricas de rendimiento
por ejecución: latencia, tokens, CPU/RAM, éxito/fallo y clasificación de riesgo.
Cada registro se persiste como una línea JSON en logs/execution_logs.jsonl (append-only).
"""

import time
import json
import os
import uuid
import psutil
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult


class ObservabilityCallbackHandler(BaseCallbackHandler):
    """
    Callback de LangChain que intercepta eventos del ciclo de vida del agente
    para registrar métricas de observabilidad sin alterar la lógica del flujo.
    """

    def __init__(self):
        self.execution_id = str(uuid.uuid4())
        self.start_time = time.perf_counter()
        self.tool_starts: Dict[str, float] = {}
        self.tool_latencies: Dict[str, float] = {}
        self.tool_status: Dict[str, str] = {}
        self.input_tokens = 0
        self.output_tokens = 0
        self.total_tokens = 0
        self.risk_classification = "No evaluado"
        self.log_dir = "logs"
        self.log_file = os.path.join(self.log_dir, "execution_logs.jsonl")
        # Captura de recursos al inicio de la ejecución
        self.cpu_start = psutil.cpu_percent(interval=None)
        self.ram_start = psutil.virtual_memory().percent

        os.makedirs(self.log_dir, exist_ok=True)

    # ── Eventos LLM ────────────────────────────────────────────────
    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> Any:
        """Captura tokens consumidos al finalizar cada llamada al LLM."""
        if response.llm_output and isinstance(response.llm_output, dict):
            usage = response.llm_output.get("token_usage", {})
            if usage:
                self.input_tokens += usage.get("prompt_tokens", 0)
                self.output_tokens += usage.get("completion_tokens", 0)
                self.total_tokens += usage.get("total_tokens", 0)

    # ── Eventos de Herramientas ────────────────────────────────────
    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> Any:
        """Registra el instante de inicio de cada herramienta para calcular latencia."""
        tool_name = serialized.get("name", "unknown_tool")
        self.tool_starts[tool_name] = time.perf_counter()

    def on_tool_end(self, output: str, **kwargs: Any) -> Any:
        """Registra latencia y estado de éxito al completarse una herramienta."""
        tool_name = kwargs.get("name", "unknown_tool")
        if tool_name in self.tool_starts:
            latency_ms = (time.perf_counter() - self.tool_starts[tool_name]) * 1000
            self.tool_latencies[tool_name] = round(latency_ms, 2)
            self.tool_status[tool_name] = "success"

        # Extraer clasificación de riesgo de la herramienta correspondiente
        if tool_name == "evaluar_nivel_riesgo" and isinstance(output, str):
            out_upper = output.upper()
            if "ALTO" in out_upper:
                self.risk_classification = "Alto"
            elif "MEDIO" in out_upper:
                self.risk_classification = "Medio"
            elif "BAJO" in out_upper:
                self.risk_classification = "Bajo"

    def on_tool_error(self, error: BaseException, **kwargs: Any) -> Any:
        """Registra latencia y estado de fallo cuando una herramienta lanza excepción."""
        tool_name = kwargs.get("name", "unknown_tool")
        if tool_name in self.tool_starts:
            latency_ms = (time.perf_counter() - self.tool_starts[tool_name]) * 1000
            self.tool_latencies[tool_name] = round(latency_ms, 2)
        self.tool_status[tool_name] = "error"

    # ── Persistencia ───────────────────────────────────────────────
    def save_log(self):
        """
        Persiste el registro completo de la ejecución como una línea JSON
        en logs/execution_logs.jsonl. Siempre opera en modo append.
        """
        total_latency_ms = (time.perf_counter() - self.start_time) * 1000
        cpu_end = psutil.cpu_percent(interval=0.1)
        ram_end = psutil.virtual_memory().percent

        log_entry = {
            "execution_id": self.execution_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_latency_ms": round(total_latency_ms, 2),
            "tool_latencies_ms": self.tool_latencies,
            "tool_status": self.tool_status,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "risk_classification": self.risk_classification,
            "cpu_percent_start": self.cpu_start,
            "cpu_percent_end": cpu_end,
            "ram_percent_start": self.ram_start,
            "ram_percent_end": ram_end,
        }

        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
