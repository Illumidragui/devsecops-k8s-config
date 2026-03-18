#!/usr/bin/env python3
"""
enrich_sarif.py
Enriquece un archivo SARIF generado por Checkov añadiendo
el nivel de severidad correcto en cada resultado.

Uso:
    python3 enrich_sarif.py <input.sarif> [output.sarif]

    Si no se especifica output, sobreescribe el archivo de entrada.
"""

import json
import sys
from pathlib import Path

# Mapa de severidad Checkov → nivel SARIF
SEVERITY_MAP = {
    "CRITICAL": "error",
    "HIGH":     "error",
    "MEDIUM":   "warning",
    "LOW":      "note",
    "INFO":     "none",
}

DEFAULT_SEVERITY = "MEDIUM"


def enrich_sarif(input_path: str, output_path: str) -> None:
    path = Path(input_path)

    if not path.exists():
        print(f"[ERROR] Archivo no encontrado: {input_path}", file=sys.stderr)
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        sarif = json.load(f)

    total = 0
    enriched = 0

    for run in sarif.get("runs", []):
        # Indexar reglas por ID para acceder rápido a sus propiedades
        rules = {
            rule["id"]: rule
            for rule in run.get("tool", {}).get("driver", {}).get("rules", [])
        }

        for result in run.get("results", []):
            total += 1
            rule_id = result.get("ruleId")
            rule = rules.get(rule_id, {})

            # Intentar extraer severidad desde las propiedades de la regla
            severity = (
                rule.get("properties", {}).get("severity") or
                rule.get("properties", {}).get("check_type") or
                DEFAULT_SEVERITY
            ).upper()

            sarif_level = SEVERITY_MAP.get(severity, "warning")

            # Solo enriquecer si el nivel no estaba ya correctamente asignado
            if result.get("level") != sarif_level:
                result["level"] = sarif_level
                enriched += 1

            # Asegurar que la severidad queda también en properties del resultado
            result.setdefault("properties", {})["severity"] = severity

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(sarif, f, indent=2)

    print(f"[OK] {enriched}/{total} resultados enriquecidos → {output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    input_file  = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else input_file

    enrich_sarif(input_file, output_file)