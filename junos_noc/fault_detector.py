"""
Automated Fault Detection Engine for Junos Networks.

Analyzes operational telemetry collected from Junos devices against
expected inventory baselines and engineering rules. Identifies interface failures,
missing routes, broken OSPF adjacencies, and hardware performance anomalies.
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger("junos_noc.fault_detector")


class FaultSeverity:
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"
    OK = "OK"


class FaultDetector:
    """Evaluates telemetry data against expected baseline rules and reports detected faults."""

    def __init__(self, baseline_rules: Dict[str, Any]):
        self.rules = baseline_rules

    def analyze_device(
        self,
        device_name: str,
        device_spec: Dict[str, Any],
        health_data: Dict[str, Any],
        interface_data: Dict[str, Dict[str, Any]],
        routing_data: Dict[str, Any],
        ospf_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Executes comprehensive fault detection checks on a single device.

        :return: List of detected fault dictionaries.
        """
        faults: List[Dict[str, Any]] = []

        # 1. Health & Resource Utilization Checks
        faults.extend(self._check_health(device_name, health_data))

        # 2. Monitored Interfaces Checks
        faults.extend(self._check_interfaces(device_name, device_spec, interface_data))

        # 3. Critical Route Reachability Checks
        faults.extend(self._check_routes(device_name, device_spec, routing_data))

        # 4. OSPF Adjacency and Neighbor Checks
        faults.extend(self._check_ospf(device_name, device_spec, ospf_data))

        return faults

    def _check_health(self, device_name: str, health: Dict[str, Any]) -> List[Dict[str, Any]]:
        faults = []
        thresholds = self.rules.get("health_thresholds", {})
        max_cpu = thresholds.get("max_cpu_percent", 80.0)
        max_mem = thresholds.get("max_memory_percent", 85.0)

        cpu = health.get("cpu_load_percent", 0.0)
        mem = health.get("memory_percent", 0.0)

        if cpu > max_cpu:
            faults.append({
                "fault_id": f"FAULT-HEALTH-CPU-{device_name}",
                "device": device_name,
                "component": "HARDWARE_HEALTH",
                "severity": FaultSeverity.CRITICAL if cpu > 90.0 else FaultSeverity.WARNING,
                "title": f"High CPU Utilization ({cpu}%)",
                "description": f"CPU load average ({cpu}%) exceeds configured threshold ({max_cpu}%).",
                "remediation": "Run 'show system processes extensive' via Junos CLI to identify rogue daemons.",
            })

        if mem > max_mem:
            faults.append({
                "fault_id": f"FAULT-HEALTH-MEM-{device_name}",
                "device": device_name,
                "component": "HARDWARE_HEALTH",
                "severity": FaultSeverity.WARNING,
                "title": f"High Memory Utilization ({mem}%)",
                "description": f"Routing Engine memory utilization ({mem}%) exceeds threshold ({max_mem}%).",
                "remediation": "Investigate routing table scale or memory leaks using 'show system virtual-memory'.",
            })

        return faults

    def _check_interfaces(
        self, device_name: str, device_spec: Dict[str, Any], ifaces: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        faults = []
        monitored = device_spec.get("monitored_interfaces", [])
        iface_rules = self.rules.get("interface_rules", {})
        max_err = iface_rules.get("max_input_errors", 10)

        for if_name in monitored:
            if if_name not in ifaces:
                faults.append({
                    "fault_id": f"FAULT-IFACE-MISSING-{device_name}-{if_name}",
                    "device": device_name,
                    "component": "INTERFACE",
                    "severity": FaultSeverity.CRITICAL,
                    "title": f"Monitored Interface {if_name} Not Found",
                    "description": f"Interface {if_name} expected in inventory but absent in device RPC output.",
                    "remediation": f"Verify physical chassis slot or FPC/PIC configuration for {if_name}.",
                })
                continue

            data = ifaces[if_name]
            # Operational Down check
            if data["oper_status"] != "up":
                faults.append({
                    "fault_id": f"FAULT-IFACE-DOWN-{device_name}-{if_name}",
                    "device": device_name,
                    "component": "INTERFACE",
                    "severity": FaultSeverity.CRITICAL,
                    "title": f"Interface {if_name} Operational State is DOWN",
                    "description": f"Interface {if_name} is administratively {data['admin_status']} but operational state is {data['oper_status']}.",
                    "remediation": f"Inspect transceiver/cable, check remote peer interface, or toggle with 'set interfaces {if_name} disable' then commit, then delete.",
                })

            # Check input errors
            if data["input_errors"] > max_err:
                faults.append({
                    "fault_id": f"FAULT-IFACE-ERR-{device_name}-{if_name}",
                    "device": device_name,
                    "component": "INTERFACE",
                    "severity": FaultSeverity.WARNING,
                    "title": f"Input Errors Detected on {if_name} ({data['input_errors']} errors)",
                    "description": f"Input errors counter ({data['input_errors']}) exceeds threshold ({max_err}). Possible CRC or duplex mismatch.",
                    "remediation": f"Check optics, fiber patch cord, and run 'show interfaces {if_name} extensive'.",
                })

        return faults

    def _check_routes(
        self, device_name: str, device_spec: Dict[str, Any], routing: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        faults = []
        critical_routes = device_spec.get("critical_routes", [])
        active_destinations = set(routing.get("destinations", []))

        for route in critical_routes:
            if route not in active_destinations:
                faults.append({
                    "fault_id": f"FAULT-ROUTE-MISSING-{device_name}-{route.replace('/', '_')}",
                    "device": device_name,
                    "component": "ROUTING",
                    "severity": FaultSeverity.CRITICAL,
                    "title": f"Critical Route {route} Missing from Routing Table (inet.0)",
                    "description": f"Expected critical route prefix {route} was not found in routing table inet.0.",
                    "remediation": f"Verify OSPF export policy, upstream link state, or static route definition for {route}.",
                })

        return faults

    def _check_ospf(
        self, device_name: str, device_spec: Dict[str, Any], ospf: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        faults = []
        expected_neighbors = set(device_spec.get("expected_neighbors", []))
        current_neighbors = {n["neighbor_id"]: n for n in ospf.get("neighbors", [])}

        # Check for missing neighbors
        for exp_id in expected_neighbors:
            if exp_id not in current_neighbors:
                faults.append({
                    "fault_id": f"FAULT-OSPF-MISSING-{device_name}-{exp_id}",
                    "device": device_name,
                    "component": "OSPF",
                    "severity": FaultSeverity.CRITICAL,
                    "title": f"Missing OSPF Neighbor Adjacency with Router-ID {exp_id}",
                    "description": f"Expected OSPF neighbor {exp_id} is not present in OSPF neighbor table.",
                    "remediation": f"Verify Hello/Dead timers, Area ID matching, and MTU match on interconnecting link.",
                })
            else:
                nbr = current_neighbors[exp_id]
                if nbr["state"] != "Full":
                    faults.append({
                        "fault_id": f"FAULT-OSPF-STATE-{device_name}-{exp_id}",
                        "device": device_name,
                        "component": "OSPF",
                        "severity": FaultSeverity.CRITICAL,
                        "title": f"OSPF Neighbor {exp_id} Stuck in {nbr['state']} State",
                        "description": f"OSPF adjacency with {exp_id} on {nbr['interface']} has state {nbr['state']} (expected 'Full').",
                        "remediation": f"Run 'clear ospf neighbor {nbr['address']}' or check MTU mismatch and firewall packet filters on {nbr['interface']}.",
                    })

        return faults
# Physical link operational state validator
