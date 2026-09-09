"""
Collectors package for retrieving operational RPC telemetry from Junos devices.
"""

from junos_noc.collectors.health import HealthCollector
from junos_noc.collectors.interfaces import InterfaceCollector
from junos_noc.collectors.routing import RoutingCollector
from junos_noc.collectors.ospf import OspfCollector

__all__ = ["HealthCollector", "InterfaceCollector", "RoutingCollector", "OspfCollector"]
