"""
Structured Diagnostic Report Generator and Terminal Dashboard.

Produces JSON reports, Markdown summaries, and rich color-coded terminal
audit dashboards for Network Operations Center (NOC) teams.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import sys

# Ensure UTF-8 output encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

console = Console(highlight=False)


class DiagnosticReporter:
    """Formats and exports diagnostic audit reports in JSON, Markdown, and Terminal formats."""

    @staticmethod
    def print_terminal_summary(audit_results: Dict[str, Any]):
        """Displays rich terminal tables showing health, interfaces, routing, OSPF, and detected faults."""
        console.print("\n")
        console.print(Panel.fit(
            "[bold cyan]JUNOS-NOC: NETWORK AUDIT & DIAGNOSTIC DASHBOARD[/bold cyan]\n"
            f"[dim]Timestamp: {audit_results.get('timestamp', 'N/A')} | Devices Monitored: {len(audit_results.get('devices', {}))}[/dim]",
            border_style="cyan"
        ))

        for dev_name, data in audit_results.get("devices", {}).items():
            health = data.get("health", {})
            ifaces = data.get("interfaces", {})
            routes = data.get("routing", {})
            ospf = data.get("ospf", {})
            faults = data.get("faults", [])

            # Device Health Summary Banner
            health_color = "green" if health.get("cpu_load_percent", 0) < 80 else "red"
            console.print(f"\n[bold]{dev_name}[/bold] ({health.get('model', 'vJunos')} - Junos {health.get('version', 'N/A')})")
            console.print(f"  [{health_color}]CPU Load:[/{health_color}] {health.get('cpu_load_percent')}% | "
                          f"[cyan]Memory:[/cyan] {health.get('memory_percent')}% | "
                          f"[cyan]Uptime:[/cyan] {health.get('uptime')} | "
                          f"[cyan]Serial:[/cyan] {health.get('serial_number')}")

            # Interface Status Table
            if_table = Table(title=f"{dev_name} - Monitored Interfaces", show_header=True, header_style="bold magenta")
            if_table.add_column("Interface", style="bold")
            if_table.add_column("Admin")
            if_table.add_column("Oper")
            if_table.add_column("Speed")
            if_table.add_column("IP Address")
            if_table.add_column("Errors (Rx/Tx)")

            for if_name, if_info in ifaces.items():
                oper_style = "green" if if_info["oper_status"] == "up" else "bold red"
                err_text = f"{if_info['input_errors']}/{if_info['output_errors']}"
                err_style = "red" if if_info["input_errors"] > 0 else "dim"
                ip_str = ", ".join(if_info["ip_addresses"]) if if_info["ip_addresses"] else "unassigned"

                if_table.add_row(
                    if_name,
                    if_info["admin_status"],
                    f"[{oper_style}]{if_info['oper_status'].upper()}[/{oper_style}]",
                    if_info["speed"],
                    ip_str,
                    f"[{err_style}]{err_text}[/{err_style}]"
                )
            console.print(if_table)

            # OSPF Neighbors Table
            ospf_table = Table(title=f"{dev_name} - OSPF Neighbors (Area 0.0.0.0)", show_header=True, header_style="bold green")
            ospf_table.add_column("Neighbor ID")
            ospf_table.add_column("Interface")
            ospf_table.add_column("IP Address")
            ospf_table.add_column("Adjacency State")
            ospf_table.add_column("Dead Timer (s)")

            for nbr in ospf.get("neighbors", []):
                state_style = "bold green" if nbr["state"] == "Full" else "bold red"
                ospf_table.add_row(
                    nbr["neighbor_id"],
                    nbr["interface"],
                    nbr["address"],
                    f"[{state_style}]{nbr['state']}[/{state_style}]",
                    str(nbr["dead_time_seconds"])
                )
            console.print(ospf_table)

            # Routes Breakdown Snippet
            proto_dist = ", ".join([f"{p}: {c}" for p, c in routes.get("protocol_breakdown", {}).items()])
            console.print(f"  [bold]Routing Table (inet.0):[/bold] {routes.get('total_routes', 0)} active routes ({proto_dist})")

            # Faults Table for this device
            if faults:
                fault_table = Table(title=f"[bold red]ALERTS & FAULTS: {dev_name} ({len(faults)} active issues)[/bold red]", border_style="red")
                fault_table.add_column("Severity", style="bold red")
                fault_table.add_column("Component")
                fault_table.add_column("Title")
                fault_table.add_column("Actionable Remediation", style="yellow")

                for f in faults:
                    fault_table.add_row(
                        f["severity"],
                        f["component"],
                        f["title"],
                        f["remediation"]
                    )
                console.print(fault_table)
            else:
                console.print(f"  [bold green][PASS] All baseline checks passed for {dev_name}. Network operating normally.[/bold green]")

    @staticmethod
    def save_json_report(audit_results: Dict[str, Any], output_dir: str = "reports") -> str:
        """Saves full audit results to a structured JSON file."""
        os.makedirs(output_dir, exist_ok=True)
        ts_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"diagnostics_{ts_str}.json"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(audit_results, f, indent=2)

        return filepath

    @staticmethod
    def save_markdown_report(audit_results: Dict[str, Any], output_dir: str = "reports") -> str:
        """Generates a human-readable Markdown summary report."""
        os.makedirs(output_dir, exist_ok=True)
        ts_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(output_dir, f"diagnostics_{ts_str}.md")

        total_faults = sum(len(d.get("faults", [])) for d in audit_results.get("devices", {}).values())

        lines = [
            "# Junos-NOC Diagnostic & Network Health Audit Report",
            "",
            f"**Execution Timestamp:** {audit_results.get('timestamp', 'N/A')}  ",
            f"**Audit Status:** {'ATTENTION REQUIRED' if total_faults > 0 else 'NORMAL / HEALTHY'}  ",
            f"**Total Faults Detected:** {total_faults}  ",
            "",
            "---",
            "",
            "## Summary of Monitored Nodes",
            "",
            "| Device | Model | Junos Version | CPU Load | Memory | Status |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |",
        ]

        for dev_name, data in audit_results.get("devices", {}).items():
            h = data.get("health", {})
            f_count = len(data.get("faults", []))
            status_badge = f"FAILED ({f_count} Faults)" if f_count > 0 else "PASSED (Healthy)"
            lines.append(f"| {dev_name} | {h.get('model', 'N/A')} | {h.get('version', 'N/A')} | {h.get('cpu_load_percent')}% | {h.get('memory_percent')}% | {status_badge} |")

        lines.extend([
            "",
            "---",
            "",
            "## Detailed Fault Log and Remediation",
            ""
        ])

        if total_faults == 0:
            lines.append("No anomalies or faults detected. All interfaces, routes, and OSPF adjacencies match inventory baselines.")
        else:
            for dev_name, data in audit_results.get("devices", {}).items():
                for fault in data.get("faults", []):
                    lines.extend([
                        f"### [{fault['severity']}] {dev_name} - {fault['title']}",
                        f"- **Component:** `{fault['component']}`",
                        f"- **Description:** {fault['description']}",
                        f"- **Remediation Action:** `{fault['remediation']}`",
                        ""
                    ])

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return filepath
# Color-coded NOC alert table formatter
