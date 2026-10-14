"""
Interface Telemetry and Statistics Collector.

Retrieves interface operational and administrative states, speed, MTU,
IP address assignments, and traffic error/drop counters using `get_interface_information` RPC.
"""

import logging
from typing import Dict, Any, List, Union
from jnpr.junos import Device
from junos_noc.mock_device import MockDevice

logger = logging.getLogger("junos_noc.collectors.interfaces")


class InterfaceCollector:
    """Collects physical and logical interface statistics and health states."""

    def __init__(self, device: Union[Device, MockDevice]):
        self.device = device

    def collect(self) -> Dict[str, Dict[str, Any]]:
        """
        Executes `get_interface_information` RPC and parses operational telemetry.

        :return: Dict mapping interface name to interface state and statistics.
        """
        interfaces: Dict[str, Dict[str, Any]] = {}

        try:
            rpc_res = self.device.rpc.get_interface_information()
            for phy in rpc_res.findall(".//physical-interface"):
                name_el = phy.find("name")
                if name_el is None or not name_el.text:
                    continue
                name = name_el.text.strip()

                admin_status = self._get_text(phy, "admin-status", default="unknown").lower()
                oper_status = self._get_text(phy, "oper-status", default="unknown").lower()
                speed = self._get_text(phy, "speed", default="n/a")
                mtu = self._get_text(phy, "mtu", default="n/a")

                # Parse errors
                rx_errors = int(self._get_text(phy, ".//input-errors", default="0"))
                tx_errors = int(self._get_text(phy, ".//output-errors", default="0"))
                rx_drops = int(self._get_text(phy, ".//input-drops", default="0"))
                tx_drops = int(self._get_text(phy, ".//output-drops", default="0"))

                # Parse assigned IP addresses from logical units
                ip_addresses: List[str] = []
                for log in phy.findall(".//logical-interface"):
                    for addr in log.findall(".//interface-address"):
                        ifa_local = self._get_text(addr, "ifa-local")
                        if ifa_local:
                            ip_addresses.append(ifa_local)

                interfaces[name] = {
                    "name": name,
                    "admin_status": admin_status,
                    "oper_status": oper_status,
                    "speed": speed,
                    "mtu": mtu,
                    "ip_addresses": ip_addresses,
                    "input_errors": rx_errors,
                    "output_errors": tx_errors,
                    "input_drops": rx_drops,
                    "output_drops": tx_drops,
                    "is_up": (admin_status == "up" and oper_status == "up"),
                }
        except Exception as e:
            logger.error("Error retrieving interface information: %s", e)

        return interfaces

    @staticmethod
    def _get_text(element, path: str, default: str = "") -> str:
        found = element.find(path)
        if found is not None and found.text:
            return found.text.strip()
        return default
