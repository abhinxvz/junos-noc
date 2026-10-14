"""
Routing Table and RIB Collector.

Retrieves Junos routing tables (inet.0), destination prefixes, next-hops,
exit interfaces, and routing protocol breakdowns via `get_route_information` RPC.
"""

import logging
from typing import Dict, Any, List, Union
from jnpr.junos import Device
from junos_noc.mock_device import MockDevice

logger = logging.getLogger("junos_noc.collectors.routing")


class RoutingCollector:
    """Extracts and parses Junos routing tables and prefix availability."""

    def __init__(self, device: Union[Device, MockDevice]):
        self.device = device

    def collect(self, table: str = "inet.0") -> Dict[str, Any]:
        """
        Executes `get_route_information` RPC and parses RIB entries.

        :param table: Routing table to query (defaults to 'inet.0').
        :return: Dict containing total count, protocol breakdown, and route list.
        """
        routes: List[Dict[str, Any]] = []
        protocols_count: Dict[str, int] = {}

        try:
            rpc_res = self.device.rpc.get_route_information(table=table)
            for rt in rpc_res.findall(".//rt"):
                dest_el = rt.find("rt-destination")
                if dest_el is None or not dest_el.text:
                    continue
                destination = dest_el.text.strip()

                for entry in rt.findall(".//rt-entry"):
                    proto = self._get_text(entry, "protocol-name", default="Unknown")
                    metric = self._get_text(entry, "metric", default="0")

                    nh_ip = self._get_text(entry, ".//nh/to", default="Direct")
                    via_iface = self._get_text(entry, ".//nh/via", default="")

                    route_info = {
                        "destination": destination,
                        "protocol": proto,
                        "metric": metric,
                        "next_hop": nh_ip,
                        "interface": via_iface,
                    }
                    routes.append(route_info)
                    protocols_count[proto] = protocols_count.get(proto, 0) + 1

        except Exception as e:
            logger.error("Error retrieving routing information for %s: %s", table, e)

        return {
            "table": table,
            "total_routes": len(routes),
            "protocol_breakdown": protocols_count,
            "routes": routes,
            "destinations": [r["destination"] for r in routes],
        }

    @staticmethod
    def _get_text(element, path: str, default: str = "") -> str:
        found = element.find(path)
        if found is not None and found.text:
            return found.text.strip()
        return default
