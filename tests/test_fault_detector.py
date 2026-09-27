"""
Unit tests for the Fault Detection Engine.
"""

import pytest
from junos_noc.mock_device import MockDevice
from junos_noc.collectors import HealthCollector, InterfaceCollector, RoutingCollector, OspfCollector
from junos_noc.fault_detector import FaultDetector, FaultSeverity


@pytest.fixture
def baseline_rules():
    return {
        "health_thresholds": {
            "max_cpu_percent": 80.0,
            "max_memory_percent": 85.0,
        },
        "interface_rules": {
            "max_input_errors": 10,
        },
    }


@pytest.fixture
def r1_spec():
    return {
        "name": "R1-CORE",
        "expected_neighbors": ["10.0.0.2", "10.0.0.3"],
        "monitored_interfaces": ["ge-0/0/0", "ge-0/0/1", "lo0"],
        "critical_routes": ["0.0.0.0/0", "10.0.0.2/32", "192.168.30.0/24"],
    }


def test_healthy_network_no_faults(baseline_rules, r1_spec):
    dev = MockDevice(name="R1-CORE", scenario="healthy")
    dev.open()

    health = HealthCollector(dev).collect()
    ifaces = InterfaceCollector(dev).collect()
    routing = RoutingCollector(dev).collect()
    ospf = OspfCollector(dev).collect()

    detector = FaultDetector(baseline_rules)
    faults = detector.analyze_device("R1-CORE", r1_spec, health, ifaces, routing, ospf)

    assert len(faults) == 0


def test_detect_interface_failure(baseline_rules, r1_spec):
    dev = MockDevice(name="R1-CORE", scenario="fault_interface")
    dev.open()

    health = HealthCollector(dev).collect()
    ifaces = InterfaceCollector(dev).collect()
    routing = RoutingCollector(dev).collect()
    ospf = OspfCollector(dev).collect()

    detector = FaultDetector(baseline_rules)
    faults = detector.analyze_device("R1-CORE", r1_spec, health, ifaces, routing, ospf)

    assert len(faults) >= 1
    oper_down_faults = [f for f in faults if f["component"] == "INTERFACE" and f["severity"] == FaultSeverity.CRITICAL]
    assert len(oper_down_faults) == 1
    assert "ge-0/0/1" in oper_down_faults[0]["title"]


def test_detect_missing_route(baseline_rules, r1_spec):
    dev = MockDevice(name="R1-CORE", scenario="fault_route")
    dev.open()

    health = HealthCollector(dev).collect()
    ifaces = InterfaceCollector(dev).collect()
    routing = RoutingCollector(dev).collect()
    ospf = OspfCollector(dev).collect()

    detector = FaultDetector(baseline_rules)
    faults = detector.analyze_device("R1-CORE", r1_spec, health, ifaces, routing, ospf)

    route_faults = [f for f in faults if f["component"] == "ROUTING"]
    assert len(route_faults) == 1
    assert "192.168.30.0/24" in route_faults[0]["title"]


def test_detect_ospf_adjacency_down(baseline_rules, r1_spec):
    dev = MockDevice(name="R1-CORE", scenario="fault_ospf")
    dev.open()

    health = HealthCollector(dev).collect()
    ifaces = InterfaceCollector(dev).collect()
    routing = RoutingCollector(dev).collect()
    ospf = OspfCollector(dev).collect()

    detector = FaultDetector(baseline_rules)
    faults = detector.analyze_device("R1-CORE", r1_spec, health, ifaces, routing, ospf)

    ospf_faults = [f for f in faults if f["component"] == "OSPF"]
    assert len(ospf_faults) == 1
    assert "10.0.0.3" in ospf_faults[0]["title"]
    assert "Init" in ospf_faults[0]["description"]
# Fault detection coverage across simulated scenarios
