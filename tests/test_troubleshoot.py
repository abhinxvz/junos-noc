"""
Unit tests for Network Troubleshooting and Recovery module.
"""

from junos_noc.mock_device import MockDevice
from junos_noc.troubleshoot import NetworkTroubleshooter


def test_ping_success():
    dev = MockDevice(name="R1-CORE", scenario="healthy")
    troubleshooter = NetworkTroubleshooter(dev)

    res = troubleshooter.ping_test("10.0.0.2")
    assert res["success"] is True
    assert res["packet_loss_percent"] == 0.0


def test_ping_failure_during_fault():
    dev = MockDevice(name="R1-CORE", scenario="fault_interface")
    troubleshooter = NetworkTroubleshooter(dev)

    res = troubleshooter.ping_test("10.0.0.3")
    assert res["success"] is False
    assert res["packet_loss_percent"] == 100.0


def test_bounce_interface_recovers():
    dev = MockDevice(name="R1-CORE", scenario="fault_interface")
    troubleshooter = NetworkTroubleshooter(dev)

    # Initial check fails
    res_fail = troubleshooter.ping_test("10.0.0.3")
    assert res_fail["success"] is False

    # Perform remediation bounce
    bounce_res = troubleshooter.bounce_interface("ge-0/0/1")
    assert bounce_res["status"] == "RECOVERED"

    # Post-remediation ping passes
    res_pass = troubleshooter.ping_test("10.0.0.3")
    assert res_pass["success"] is True
