"""
OSPF Routing Protocol Adjacency Collector.

Monitors Junos OSPF neighbor states, interface adjacencies, peer Router-IDs,
and dead-timer countdowns using `get_ospf_neighbor_information` RPC.
"""

import logging
from typing import Dict, Any, List, Union
from jnpr.junos import Device
from junos_noc.mock_device import MockDevice

logger = logging.getLogger("junos_noc.collectors.ospf")


class OspfCollector:
    """Collects OSPF neighbor operational state and adjacency health."""

    def __init__(self, device: Union[Device, MockDevice]):
        self.device = device

    def collect(self) -> Dict[str, Any]:
        """
        Executes `get_ospf_neighbor_information` RPC and parses neighbor states.

        :return: Dict containing neighbor list, adjacency counts, and health status.
        """
        neighbors: List[Dict[str, Any]] = []
        full_count = 0

        try:
            rpc_res = self.device.rpc.get_ospf_neighbor_information()
            for nbr in rpc_res.findall(".//ospf-neighbor"):
                peer_id = self._get_text(nbr, "neighbor-id")
                iface = self._get_text(nbr, "interface-name")
                state = self._get_text(nbr, "ospf-neighbor-state")
                addr = self._get_text(nbr, "neighbor-address")
                dead_time = self._get_text(nbr, "dead-time", default="0")

                if state == "Full":
                    full_count += 1

                neighbors.append({
                    "neighbor_id": peer_id,
                    "interface": iface,
                    "state": state,
                    "address": addr,
                    "dead_time_seconds": dead_time,
                    "is_full": (state == "Full"),
                })
        except Exception as e:
            logger.error("Error retrieving OSPF neighbor information: %s", e)

        return {
            "total_neighbors": len(neighbors),
            "full_neighbors": full_count,
            "all_full": (len(neighbors) > 0 and len(neighbors) == full_count),
            "neighbors": neighbors,
            "neighbor_ids": [n["neighbor_id"] for n in neighbors],
        }

    @staticmethod
    def _get_text(element, path: str, default: str = "") -> str:
        found = element.find(path)
        if found is not None and found.text:
            return found.text.strip()
        return default
# Adjacency dead timer and neighbor state evaluator
