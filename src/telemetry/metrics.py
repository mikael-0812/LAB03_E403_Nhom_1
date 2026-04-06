import time
from typing import Dict, Any, List
from src.telemetry.logger import logger


class PerformanceTracker:
    """
    Tracking industry-standard metrics for LLMs.
    """

    def __init__(self):
        self.session_metrics = []

    def track_request(self, provider: str, model: str, usage: Dict[str, int], latency_ms: int):
        """
        Logs a single request metric to telemetry.
        """
        metric = {
            "provider": provider,
            "model": model,
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
            "latency_ms": latency_ms,
            "cost_estimate": self._calculate_cost(model, usage)
        }
        self.session_metrics.append(metric)
        logger.log_event("LLM_METRIC", metric)

    def track_agent_run(
        self,
        model: str,
        steps: int,
        success: bool,
        latency_ms: int,
        stop_reason: str,
        provider: str = "unknown"
    ):
        """
        Logs one full agent run.
        """
        metric = {
            "provider": provider,
            "model": model,
            "steps": steps,
            "success": success,
            "latency_ms": latency_ms,
            "stop_reason": stop_reason
        }
        self.session_metrics.append(metric)
        logger.log_event("AGENT_METRIC", metric)

    def summary(self) -> Dict[str, Any]:
        """
        Aggregate summary for quick reporting.
        """
        if not self.session_metrics:
            return {
                "num_records": 0,
                "total_latency_ms": 0,
                "avg_latency_ms": 0,
                "total_tokens": 0,
                "total_cost_estimate": 0.0
            }

        total_latency_ms = 0
        total_tokens = 0
        total_cost = 0.0

        for metric in self.session_metrics:
            total_latency_ms += metric.get("latency_ms", 0)
            total_tokens += metric.get("total_tokens", 0)
            total_cost += metric.get("cost_estimate", 0.0)

        return {
            "num_records": len(self.session_metrics),
            "total_latency_ms": total_latency_ms,
            "avg_latency_ms": total_latency_ms / len(self.session_metrics),
            "total_tokens": total_tokens,
            "total_cost_estimate": total_cost
        }

    def _calculate_cost(self, model: str, usage: Dict[str, int]) -> float:
        """
        Basic mock pricing logic.
        You can replace this later with real pricing if needed.
        """
        pricing_per_1k_tokens = {
            "gpt-4o": 0.01,
            "gpt-4o-mini": 0.0006,
            "gemini-1.5-flash": 0.002,
            "local": 0.0,
        }

        rate = pricing_per_1k_tokens.get(model, 0.01)
        return (usage.get("total_tokens", 0) / 1000) * rate


# Global tracker instance
tracker = PerformanceTracker()