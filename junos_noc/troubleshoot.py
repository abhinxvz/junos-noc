"""
Network Recovery and Troubleshooting Toolkit.

Provides active operational validation using Junos PyEZ RPC ping and traceroute,
interface bounce and recovery procedures, and post-remediation verification.
"""

import logging
from typing import Dict, Any, List, Union
from jnpr.junos import Device
from junos_noc.mock_device import MockDevice

logger = logging.getLogger("junos_noc.troubleshoot")


class NetworkTroubleshooter:
    """Executes network validation, reachability tests, and recovery actions."""

    def __init__(self, device: Union[Device, MockDevice]):
        self.device = device
        self.dev_name = getattr(device, "name", str(device.host if hasattr(device, "host") else "Unknown"))

    def ping_test(self, target_ip: str, count: int = 5) -> Dict[str, Any]:
        """
        Executes a Junos ping RPC towards target_ip.

        :param target_ip: IPv4 address to ping.
        :param count: Number of probe packets.
        :return: Dict containing packet loss percentage, packets sent/received, and status.
        """
        try:
            rpc_res = self.device.rpc.ping(host=target_ip, count=count)
            tx = int(rpc_res.findtext(".//packets-transmitted", default=str(count)))
            rx = int(rpc_res.findtext(".//packets-received", default="0"))
            loss = float(rpc_res.findtext(".//packet-loss", default="100"))
            rtt = rpc_res.findtext(".//rtt-average", default="n/a")

            is_success = (loss == 0.0 and rx > 0)
            return {
                "target": target_ip,
                "transmitted": tx,
                "received": rx,
                "packet_loss_percent": loss,
                "avg_rtt_ms": rtt,
                "success": is_success,
            }
        except Exception as e:
            logger.error("Ping RPC failed from %s to %s: %s", self.dev_name, target_ip, e)
            return {
                "target": target_ip,
                "transmitted": count,
                "received": 0,
                "packet_loss_percent": 100.0,
                "avg_rtt_ms": "n/a",
                "success": False,
                "error": str(e),
            }

    def run_connectivity_matrix(self, targets: List[str]) -> Dict[str, Any]:
        """Runs ping tests against multiple endpoints and returns connectivity results."""
        results = {}
        all_ok = True

        for ip in targets:
            res = self.ping_test(ip)
            results[ip] = res
            if not res["success"]:
                all_ok = False

        return {
            "source_device": self.dev_name,
            "overall_healthy": all_ok,
            "targets": results,
        }

    def execute_cli_command(self, command: str) -> str:
        """Executes an operational Junos CLI command and returns text output."""
        try:
            return self.device.cli(command)
        except Exception as e:
            return f"Error executing CLI '{command}': {e}"

    def bounce_interface(self, interface_name: str) -> Dict[str, Any]:
        """
        Simulates / executes interface bounce to clear transient link faults.

        :param interface_name: Target interface to bounce (e.g. ge-0/0/1).
        """
        if isinstance(self.device, MockDevice):
            # If in mock device, simulate recovery by toggling scenario
            self.device.scenario = "healthy"
            return {
                "device": self.dev_name,
                "interface": interface_name,
                "action": "bounce",
                "status": "RECOVERED",
                "message": f"Interface {interface_name} administrative cycle completed. Link restored to UP state.",
            }

        # On live device, we would execute configuration RPC or CLI
        try:
            self.device.cli(f"request interface cycle {interface_name}")
            return {
                "device": self.dev_name,
                "interface": interface_name,
                "action": "bounce",
                "status": "EXECUTED",
                "message": f"Successfully issued link cycle request for {interface_name}.",
            }
        except Exception as e:
            return {
                "device": self.dev_name,
                "interface": interface_name,
                "action": "bounce",
                "status": "FAILED",
                "error": str(e),
            }
# Link flap recovery and bounce logic
