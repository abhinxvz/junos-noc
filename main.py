"""
JunosNOC: Network Automation & Fault Detection CLI.

Main operational command-line interface for Juniper network audits,
operational telemetry collection, automated fault detection, and recovery verification.
"""

import argparse
import sys
import yaml
from datetime import datetime
from typing import Dict, Any, List

# Ensure UTF-8 output encoding on Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from rich.console import Console
from rich.panel import Panel

from junos_noc.client import DeviceManager
from junos_noc.collectors import HealthCollector, InterfaceCollector, RoutingCollector, OspfCollector
from junos_noc.fault_detector import FaultDetector
from junos_noc.reporter import DiagnosticReporter
from junos_noc.troubleshoot import NetworkTroubleshooter

console = Console(highlight=False)


def load_yaml(file_path: str) -> Dict[str, Any]:
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_audit(
    device_filter: str = "all",
    mock: bool = True,
    scenario: str = "healthy",
    save_reports: bool = True,
) -> Dict[str, Any]:
    """Runs end-to-end audit and fault detection on inventory devices."""
    inventory = load_yaml("inventory/devices.yaml")
    rules = load_yaml("rules/baseline_rules.yaml")

    devices_to_check = inventory.get("devices", [])
    if device_filter != "all":
        devices_to_check = [d for d in devices_to_check if d["name"].lower() == device_filter.lower()]

    if not devices_to_check:
        console.print(f"[bold red]Error: No devices found matching filter '{device_filter}'[/bold red]")
        sys.exit(1)

    detector = FaultDetector(baseline_rules=rules)
    audit_results: Dict[str, Any] = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "devices": {},
    }

    console.print(f"[cyan]Initiating audit on {len(devices_to_check)} device(s) [Mode: {'MOCK SIMULATION' if mock else 'LIVE NETCONF'}]...[/cyan]")

    for dev_spec in devices_to_check:
        name = dev_spec["name"]
        console.print(f"Connecting to [bold]{name}[/bold] ({dev_spec['host']})...")

        try:
            device = DeviceManager.get_device(
                host=dev_spec["host"],
                user=dev_spec.get("username", "junos-admin"),
                password=dev_spec.get("password"),
                port=dev_spec.get("port", 830),
                mock=mock,
                mock_scenario=scenario,
                device_name=name,
            )

            # Collect Operational RPCs
            health_data = HealthCollector(device).collect()
            interface_data = InterfaceCollector(device).collect()
            routing_data = RoutingCollector(device).collect(table="inet.0")
            ospf_data = OspfCollector(device).collect()

            # Analyze for faults
            faults = detector.analyze_device(
                device_name=name,
                device_spec=dev_spec,
                health_data=health_data,
                interface_data=interface_data,
                routing_data=routing_data,
                ospf_data=ospf_data,
            )

            audit_results["devices"][name] = {
                "health": health_data,
                "interfaces": interface_data,
                "routing": routing_data,
                "ospf": ospf_data,
                "faults": faults,
            }

            device.close()

        except Exception as e:
            console.print(f"[bold red]Failed to collect data from {name}: {e}[/bold red]")
            audit_results["devices"][name] = {"error": str(e), "faults": []}

    # Display Dashboard in Terminal
    DiagnosticReporter.print_terminal_summary(audit_results)

    # Save Reports
    if save_reports:
        json_path = DiagnosticReporter.save_json_report(audit_results)
        md_path = DiagnosticReporter.save_markdown_report(audit_results)
        console.print(f"\n[green][OK] Diagnostic JSON Report saved to: [bold]{json_path}[/bold][/green]")
        console.print(f"[green][OK] Summary Markdown Report saved to: [bold]{md_path}[/bold][/green]\n")

    return audit_results


def run_verify(mock: bool = True):
    """Executes network ping verification across all loopbacks."""
    inventory = load_yaml("inventory/devices.yaml")
    devices = inventory.get("devices", [])

    all_loopbacks = [d["loopback"] for d in devices]

    console.print(Panel.fit("[bold green]JUNOS-NOC: NETWORK CONNECTIVITY VERIFICATION[/bold green]"))

    for dev_spec in devices:
        name = dev_spec["name"]
        console.print(f"\n[bold]{name}[/bold] validating reachability to all network loopbacks...")
        device = DeviceManager.get_device(
            host=dev_spec["host"],
            user=dev_spec.get("username", "junos-admin"),
            mock=mock,
            mock_scenario="healthy",
            device_name=name,
        )

        troubleshooter = NetworkTroubleshooter(device)
        res = troubleshooter.run_connectivity_matrix(all_loopbacks)

        for target_ip, p_res in res["targets"].items():
            if p_res["success"]:
                console.print(f"  [green][PASS] Ping to {target_ip}: SUCCESS (0% loss, avg {p_res['avg_rtt_ms']} ms)[/green]")
            else:
                console.print(f"  [bold red][FAIL] Ping to {target_ip}: FAILED (100% loss)[/bold red]")

        device.close()


def run_simulation(fault_type: str = "fault_interface"):
    """
    Simulates a live network fault scenario, demonstrates automated fault detection,
    and then verifies network recovery.
    """
    console.print(Panel.fit(
        f"[bold yellow]JUNOS-NOC: INCIDENT SIMULATION & RECOVERY WORKFLOW[/bold yellow]\n"
        f"Injecting Fault: [bold red]{fault_type}[/bold red]",
        border_style="yellow"
    ))

    # Step 1: Detect the fault
    console.print("\n[bold]STEP 1: Automated Detection of Active Fault...[/bold]")
    run_audit(device_filter="R1-CORE", mock=True, scenario=fault_type, save_reports=False)

    # Step 2: Trigger Remediation
    console.print("\n[bold]STEP 2: Executing NOC Automated Remediation Action...[/bold]")
    device = DeviceManager.get_device(host="192.168.1.11", mock=True, mock_scenario=fault_type, device_name="R1-CORE")
    troubleshooter = NetworkTroubleshooter(device)

    remedy_result = troubleshooter.bounce_interface("ge-0/0/1")
    console.print(f"  [cyan]{remedy_result['message']}[/cyan]")

    # Step 3: Verify Recovery
    console.print("\n[bold]STEP 3: Validating Network Recovery & Convergence...[/bold]")
    ping_check = troubleshooter.ping_test("10.0.0.3")
    if ping_check["success"]:
        console.print(f"  [bold green][PASS] Network Restored! Ping to R3-EDGE (10.0.0.3) successful (0% loss).[/bold green]")
    else:
        console.print(f"  [bold red][FAIL] Ping failed during recovery verification.[/bold red]")

    device.close()


def main():
    parser = argparse.ArgumentParser(description="JunosNOC: Network Automation & Fault Detection Engine")
    subparsers = parser.add_subparsers(dest="command", help="Operational Subcommands")

    # Subcommand: audit
    audit_parser = subparsers.add_parser("audit", help="Run comprehensive network audit and generate diagnostic reports")
    audit_parser.add_argument("--device", default="all", help="Target device name or 'all'")
    audit_parser.add_argument("--mock", action="store_true", default=True, help="Run in mock/offline mode (default: True)")
    audit_parser.add_argument("--live", dest="mock", action="store_false", help="Connect to live routers via NETCONF port 830")
    audit_parser.add_argument("--scenario", default="healthy", choices=["healthy", "fault_interface", "fault_ospf", "fault_route", "fault_cpu"], help="Mock fault scenario to simulate")

    # Subcommand: detect
    detect_parser = subparsers.add_parser("detect", help="Run automated fault detection")
    detect_parser.add_argument("--device", default="all")
    detect_parser.add_argument("--scenario", default="fault_interface", choices=["healthy", "fault_interface", "fault_ospf", "fault_route", "fault_cpu"])

    # Subcommand: verify
    verify_parser = subparsers.add_parser("verify", help="Validate ping reachability matrix across the topology")
    verify_parser.add_argument("--mock", action="store_true", default=True)

    # Subcommand: simulate
    sim_parser = subparsers.add_parser("simulate", help="Run fault injection and remediation workflow demo")
    sim_parser.add_argument("--fault", default="fault_interface", choices=["fault_interface", "fault_ospf", "fault_route", "fault_cpu"])

    args = parser.parse_args()

    if args.command == "audit" or args.command is None:
        scenario = getattr(args, "scenario", "healthy")
        mock = getattr(args, "mock", True)
        device = getattr(args, "device", "all")
        run_audit(device_filter=device, mock=mock, scenario=scenario)

    elif args.command == "detect":
        run_audit(device_filter=args.device, mock=True, scenario=args.scenario)

    elif args.command == "verify":
        run_verify(mock=args.mock)

    elif args.command == "simulate":
        run_simulation(fault_type=args.fault)


if __name__ == "__main__":
    main()
# CLI flag normalization for live vs mock testing
