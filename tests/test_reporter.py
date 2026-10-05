"""
Unit tests for the Diagnostic Reporter module.
"""

import os
import json
from junos_noc.reporter import DiagnosticReporter


def test_save_json_and_markdown_reports(tmp_path):
    audit_data = {
        "timestamp": "2026-10-15 17:00:00 UTC",
        "devices": {
            "R1-CORE": {
                "health": {"model": "vJunos", "version": "23.2", "cpu_load_percent": 10.0, "memory_percent": 30.0},
                "faults": [],
            }
        }
    }

    out_dir = str(tmp_path / "reports")
    json_file = DiagnosticReporter.save_json_report(audit_data, output_dir=out_dir)
    md_file = DiagnosticReporter.save_markdown_report(audit_data, output_dir=out_dir)

    assert os.path.exists(json_file)
    assert os.path.exists(md_file)

    with open(json_file, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert "R1-CORE" in loaded["devices"]

    with open(md_file, "r", encoding="utf-8") as f:
        md_text = f.read()
    assert "R1-CORE" in md_text
    assert "NORMAL / HEALTHY" in md_text
