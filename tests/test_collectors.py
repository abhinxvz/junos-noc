"""
Unit tests for Junos operational RPC collectors.
"""

import pytest
from junos_noc.mock_device import MockDevice
from junos_noc.collectors import HealthCollector, InterfaceCollector, RoutingCollector, OspfCollector


@pytest.fixture
def mock_device():
    dev = MockDevice(name="R1-CORE", scenario="healthy")
    dev.open()
    yield dev
    dev.close()


def test_health_collector(mock_device):
    collector = HealthCollector(mock_device)
    health = collector.collect()

    assert health["hostname"] == "R1-CORE"
    assert health["model"] == "vJunos-router"
    assert health["version"] == "23.2R1.14"
    assert health["cpu_load_percent"] == 12.0
    assert health["memory_percent"] == 42.0
    assert health["uptime_hours"] > 300.0


def test_interface_collector(mock_device):
    collector = InterfaceCollector(mock_device)
    ifaces = collector.collect()

    assert "ge-0/0/0" in ifaces
    assert "ge-0/0/1" in ifaces
    assert ifaces["ge-0/0/0"]["oper_status"] == "up"
    assert ifaces["ge-0/0/0"]["admin_status"] == "up"
    assert ifaces["ge-0/0/0"]["is_up"] is True
    assert "10.10.12.1/30" in ifaces["ge-0/0/0"]["ip_addresses"]


def test_routing_collector(mock_device):
    collector = RoutingCollector(mock_device)
    routing = collector.collect(table="inet.0")

    assert routing["table"] == "inet.0"
    assert routing["total_routes"] == 10
    assert "0.0.0.0/0" in routing["destinations"]
    assert "10.0.0.1/32" in routing["destinations"]
    assert "Static" in routing["protocol_breakdown"]
    assert "OSPF" in routing["protocol_breakdown"]


def test_ospf_collector(mock_device):
    collector = OspfCollector(mock_device)
    ospf = collector.collect()

    assert ospf["total_neighbors"] == 2
    assert ospf["full_neighbors"] == 2
    assert ospf["all_full"] is True
    assert "10.0.0.2" in ospf["neighbor_ids"]
    assert "10.0.0.3" in ospf["neighbor_ids"]
