"""Métricas no formato de texto Prometheus, sem dependências (≤50 linhas).

Não requer prometheus_client: gera a exposição textual à mão. Alimentado
pelas contagens acumuladas do EventBus (via auditoria) + gauges do app.
"""
from __future__ import annotations

import time

_START = time.time()


def render_metrics(counts: dict[str, int] | None = None,
                   gauges: dict[str, float] | None = None) -> str:
    lines: list[str] = []
    lines.append("# HELP ants_events_total Total de eventos por tipo")
    lines.append("# TYPE ants_events_total counter")
    for etype, value in sorted((counts or {}).items()):
        lines.append(f'ants_events_total{{type="{etype}"}} {value}')

    lines.append("# HELP ants_uptime_seconds Tempo de atividade")
    lines.append("# TYPE ants_uptime_seconds gauge")
    lines.append(f"ants_uptime_seconds {time.time() - _START:.1f}")

    for name, value in (gauges or {}).items():
        lines.append(f"# TYPE ants_{name} gauge")
        lines.append(f"ants_{name} {value}")
    return "\n".join(lines) + "\n"
