"""
Mock Junos Device Implementation for offline testing and lab simulation.

Simulates Junos PyEZ Device operational RPCs with XML/Python dictionaries
representing R1-CORE, R2-DIST, and R3-EDGE in both normal and fault conditions.
"""

from typing import Dict, Any, Optional
import xml.etree.ElementTree as ET


class MockRPC:
    """Mock RPC handler mimicking Device.rpc.* methods returning parsed structures or XML."""

    def __init__(self, device_name: str, scenario: str = "healthy"):
        self.device_name = device_name
        self.scenario = scenario

    def get_system_uptime_information(self) -> ET.Element:
        uptime_str = "14 days, 6 hours, 22 minutes"
        cpu_load = "12" if self.scenario != "fault_cpu" else "94"
        memory_usage = "42" if self.scenario != "fault_memory" else "89"

        xml_data = f"""
        <system-uptime-information>
            <current-time>2026-10-15 17:00:00 UTC</current-time>
            <system-booted-time>2026-10-01 10:38:00 UTC</system-booted-time>
            <uptime-information>
                <active-user-count>1</active-user-count>
                <load-average-1>{cpu_load}%</load-average-1>
                <load-average-5>10%</load-average-5>
                <up-time>{uptime_str}</up-time>
            </uptime-information>
            <memory-utilization>{memory_usage}</memory-utilization>
        </system-uptime-information>
        """
        return ET.fromstring(xml_data.strip())

    def get_interface_information(self, terse: bool = False, interface_name: Optional[str] = None) -> ET.Element:
        root = ET.Element("interface-information")

        # Define default states for interfaces based on scenario
        interfaces_data = [
            {"name": "ge-0/0/0", "admin": "up", "oper": "up", "ip": "10.10.12.1/30", "rx_err": "0", "tx_err": "0"},
            {"name": "ge-0/0/1", "admin": "up", "oper": "up", "ip": "10.10.13.1/30", "rx_err": "0", "tx_err": "0"},
            {"name": "ge-0/0/2", "admin": "up", "oper": "up", "ip": "192.168.10.1/24", "rx_err": "0", "tx_err": "0"},
            {"name": "ge-0/0/3", "admin": "up", "oper": "up", "ip": "198.51.100.2/30", "rx_err": "0", "tx_err": "0"},
            {"name": "lo0", "admin": "up", "oper": "up", "ip": "10.0.0.1/32", "rx_err": "0", "tx_err": "0"},
        ]

        if self.device_name == "R2-DIST":
            interfaces_data = [
                {"name": "ge-0/0/0", "admin": "up", "oper": "up", "ip": "10.10.12.2/30", "rx_err": "0", "tx_err": "0"},
                {"name": "ge-0/0/1", "admin": "up", "oper": "up", "ip": "10.10.23.1/30", "rx_err": "0", "tx_err": "0"},
                {"name": "ge-0/0/2", "admin": "up", "oper": "up", "ip": "192.168.20.1/24", "rx_err": "0", "tx_err": "0"},
                {"name": "lo0", "admin": "up", "oper": "up", "ip": "10.0.0.2/32", "rx_err": "0", "tx_err": "0"},
            ]
        elif self.device_name == "R3-EDGE":
            interfaces_data = [
                {"name": "ge-0/0/0", "admin": "up", "oper": "up", "ip": "10.10.13.2/30", "rx_err": "0", "tx_err": "0"},
                {"name": "ge-0/0/1", "admin": "up", "oper": "up", "ip": "10.10.23.2/30", "rx_err": "0", "tx_err": "0"},
                {"name": "ge-0/0/2", "admin": "up", "oper": "up", "ip": "192.168.30.1/24", "rx_err": "0", "tx_err": "0"},
                {"name": "lo0", "admin": "up", "oper": "up", "ip": "10.0.0.3/32", "rx_err": "0", "tx_err": "0"},
            ]

        # Inject fault if scenario requested
        if self.scenario == "fault_interface" and self.device_name == "R1-CORE":
            for iface in interfaces_data:
                if iface["name"] == "ge-0/0/1":
                    iface["oper"] = "down"
                    iface["rx_err"] = "142"

        for iface in interfaces_data:
            if interface_name and iface["name"] != interface_name:
                continue

            phy = ET.SubElement(root, "physical-interface")
            ET.SubElement(phy, "name").text = iface["name"]
            ET.SubElement(phy, "admin-status").text = iface["admin"]
            ET.SubElement(phy, "oper-status").text = iface["oper"]
            ET.SubElement(phy, "speed").text = "1Gbps"
            ET.SubElement(phy, "mtu").text = "1500"

            errs = ET.SubElement(phy, "input-error-list")
            ET.SubElement(errs, "input-errors").text = iface["rx_err"]
            ET.SubElement(errs, "input-drops").text = "0"
            ET.SubElement(errs, "output-errors").text = iface["tx_err"]
            ET.SubElement(errs, "output-drops").text = "0"

            log = ET.SubElement(phy, "logical-interface")
            ET.SubElement(log, "name").text = f"{iface['name']}.0"
            fam = ET.SubElement(log, "address-family")
            ET.SubElement(fam, "address-family-name").text = "inet"
            addr = ET.SubElement(fam, "interface-address")
            ET.SubElement(addr, "ifa-local").text = iface["ip"]

        return root

    def get_route_information(self, table: str = "inet.0") -> ET.Element:
        root = ET.Element("route-information")
        tbl = ET.SubElement(root, "route-table")
        ET.SubElement(tbl, "table-name").text = table

        routes = []
        if self.device_name == "R1-CORE":
            routes = [
                {"dest": "0.0.0.0/0", "proto": "Static", "nh": "198.51.100.1", "iface": "ge-0/0/3.0", "metric": "5"},
                {"dest": "10.0.0.1/32", "proto": "Direct", "nh": "lo0.0", "iface": "lo0.0", "metric": "0"},
                {"dest": "10.0.0.2/32", "proto": "OSPF", "nh": "10.10.12.2", "iface": "ge-0/0/0.0", "metric": "10"},
                {"dest": "10.0.0.3/32", "proto": "OSPF", "nh": "10.10.13.2", "iface": "ge-0/0/1.0", "metric": "10"},
                {"dest": "10.10.12.0/30", "proto": "Direct", "nh": "ge-0/0/0.0", "iface": "ge-0/0/0.0", "metric": "0"},
                {"dest": "10.10.13.0/30", "proto": "Direct", "nh": "ge-0/0/1.0", "iface": "ge-0/0/1.0", "metric": "0"},
                {"dest": "10.10.23.0/30", "proto": "OSPF", "nh": "10.10.12.2", "iface": "ge-0/0/0.0", "metric": "20"},
                {"dest": "192.168.10.0/24", "proto": "Direct", "nh": "ge-0/0/2.0", "iface": "ge-0/0/2.0", "metric": "0"},
                {"dest": "192.168.20.0/24", "proto": "OSPF", "nh": "10.10.12.2", "iface": "ge-0/0/0.0", "metric": "20"},
                {"dest": "192.168.30.0/24", "proto": "OSPF", "nh": "10.10.13.2", "iface": "ge-0/0/1.0", "metric": "20"},
            ]
        elif self.device_name == "R2-DIST":
            routes = [
                {"dest": "0.0.0.0/0", "proto": "OSPF", "nh": "10.10.12.1", "iface": "ge-0/0/0.0", "metric": "10"},
                {"dest": "10.0.0.1/32", "proto": "OSPF", "nh": "10.10.12.1", "iface": "ge-0/0/0.0", "metric": "10"},
                {"dest": "10.0.0.2/32", "proto": "Direct", "nh": "lo0.0", "iface": "lo0.0", "metric": "0"},
                {"dest": "10.0.0.3/32", "proto": "OSPF", "nh": "10.10.23.2", "iface": "ge-0/0/1.0", "metric": "10"},
                {"dest": "10.10.12.0/30", "proto": "Direct", "nh": "ge-0/0/0.0", "iface": "ge-0/0/0.0", "metric": "0"},
                {"dest": "10.10.13.0/30", "proto": "OSPF", "nh": "10.10.12.1", "iface": "ge-0/0/0.0", "metric": "20"},
                {"dest": "10.10.23.0/30", "proto": "Direct", "nh": "ge-0/0/1.0", "iface": "ge-0/0/1.0", "metric": "0"},
                {"dest": "192.168.10.0/24", "proto": "OSPF", "nh": "10.10.12.1", "iface": "ge-0/0/0.0", "metric": "20"},
                {"dest": "192.168.20.0/24", "proto": "Direct", "nh": "ge-0/0/2.0", "iface": "ge-0/0/2.0", "metric": "0"},
                {"dest": "192.168.30.0/24", "proto": "OSPF", "nh": "10.10.23.2", "iface": "ge-0/0/1.0", "metric": "20"},
            ]
        elif self.device_name == "R3-EDGE":
            routes = [
                {"dest": "0.0.0.0/0", "proto": "OSPF", "nh": "10.10.13.1", "iface": "ge-0/0/0.0", "metric": "10"},
                {"dest": "10.0.0.1/32", "proto": "OSPF", "nh": "10.10.13.1", "iface": "ge-0/0/0.0", "metric": "10"},
                {"dest": "10.0.0.2/32", "proto": "OSPF", "nh": "10.10.23.1", "iface": "ge-0/0/1.0", "metric": "10"},
                {"dest": "10.0.0.3/32", "proto": "Direct", "nh": "lo0.0", "iface": "lo0.0", "metric": "0"},
                {"dest": "10.10.12.0/30", "proto": "OSPF", "nh": "10.10.13.1", "iface": "ge-0/0/0.0", "metric": "20"},
                {"dest": "10.10.13.0/30", "proto": "Direct", "nh": "ge-0/0/0.0", "iface": "ge-0/0/0.0", "metric": "0"},
                {"dest": "10.10.23.0/30", "proto": "Direct", "nh": "ge-0/0/1.0", "iface": "ge-0/0/1.0", "metric": "0"},
                {"dest": "192.168.10.0/24", "proto": "OSPF", "nh": "10.10.13.1", "iface": "ge-0/0/0.0", "metric": "20"},
                {"dest": "192.168.20.0/24", "proto": "OSPF", "nh": "10.10.23.1", "iface": "ge-0/0/1.0", "metric": "20"},
                {"dest": "192.168.30.0/24", "proto": "Direct", "nh": "ge-0/0/2.0", "iface": "ge-0/0/2.0", "metric": "0"},
            ]

        # Inject missing route fault if scenario requested
        if self.scenario == "fault_route" and self.device_name == "R1-CORE":
            routes = [r for r in routes if r["dest"] != "192.168.30.0/24"]

        for r in routes:
            rt_entry = ET.SubElement(tbl, "rt")
            ET.SubElement(rt_entry, "rt-destination").text = r["dest"]
            rt_entry_nh = ET.SubElement(rt_entry, "rt-entry")
            ET.SubElement(rt_entry_nh, "protocol-name").text = r["proto"]
            ET.SubElement(rt_entry_nh, "metric").text = r["metric"]
            nh = ET.SubElement(rt_entry_nh, "nh")
            ET.SubElement(nh, "to").text = r["nh"]
            ET.SubElement(nh, "via").text = r["iface"]

        return root

    def get_ospf_neighbor_information(self) -> ET.Element:
        root = ET.Element("ospf-neighbor-information")

        neighbors = []
        if self.device_name == "R1-CORE":
            neighbors = [
                {"peer_id": "10.0.0.2", "iface": "ge-0/0/0.0", "state": "Full", "address": "10.10.12.2", "dead_time": "36"},
                {"peer_id": "10.0.0.3", "iface": "ge-0/0/1.0", "state": "Full", "address": "10.10.13.2", "dead_time": "38"},
            ]
        elif self.device_name == "R2-DIST":
            neighbors = [
                {"peer_id": "10.0.0.1", "iface": "ge-0/0/0.0", "state": "Full", "address": "10.10.12.1", "dead_time": "35"},
                {"peer_id": "10.0.0.3", "iface": "ge-0/0/1.0", "state": "Full", "address": "10.10.23.2", "dead_time": "37"},
            ]
        elif self.device_name == "R3-EDGE":
            neighbors = [
                {"peer_id": "10.0.0.1", "iface": "ge-0/0/0.0", "state": "Full", "address": "10.10.13.1", "dead_time": "36"},
                {"peer_id": "10.0.0.2", "iface": "ge-0/0/1.0", "state": "Full", "address": "10.10.23.1", "dead_time": "39"},
            ]

        # Inject OSPF adjacency fault if scenario requested
        if self.scenario == "fault_ospf" and self.device_name == "R1-CORE":
            for n in neighbors:
                if n["peer_id"] == "10.0.0.3":
                    n["state"] = "Init"
                    n["dead_time"] = "4"

        for n in neighbors:
            nbr = ET.SubElement(root, "ospf-neighbor")
            ET.SubElement(nbr, "neighbor-id").text = n["peer_id"]
            ET.SubElement(nbr, "interface-name").text = n["iface"]
            ET.SubElement(nbr, "ospf-neighbor-state").text = n["state"]
            ET.SubElement(nbr, "neighbor-address").text = n["address"]
            ET.SubElement(nbr, "dead-time").text = n["dead_time"]

        return root

    def ping(self, host: str, count: int = 5) -> ET.Element:
        root = ET.Element("ping-results")
        ET.SubElement(root, "target-host").text = host

        # If destination is simulated broken link
        if self.scenario == "fault_interface" and host in ("10.10.13.2", "10.0.0.3") and self.device_name == "R1-CORE":
            ET.SubElement(root, "packets-transmitted").text = str(count)
            ET.SubElement(root, "packets-received").text = "0"
            ET.SubElement(root, "packet-loss").text = "100"
        else:
            ET.SubElement(root, "packets-transmitted").text = str(count)
            ET.SubElement(root, "packets-received").text = str(count)
            ET.SubElement(root, "packet-loss").text = "0"
            ET.SubElement(root, "rtt-average").text = "1.842"
        return root


class MockDevice:
    """Mock Junos PyEZ Device for running audits, tests, and fault diagnosis offline."""

    def __init__(self, host: str = "127.0.0.1", user: str = "junos-admin", name: str = "R1-CORE", scenario: str = "healthy", **kwargs):
        self.host = host
        self.user = user
        self._scenario = scenario
        self.connected = False

        self.facts: Dict[str, Any] = {
            "hostname": name,
            "version": "23.2R1.14",
            "model": "vJunos-router",
            "serialnumber": f"JNPR-VLAB-{name}",
            "personality": "JUNOS",
            "uptime": "14 days, 6 hours",
            "HOME": "/var/home/junos-admin",
            "2RE": False,
        }
        self.rpc = MockRPC(device_name=name, scenario=scenario)

    @property
    def scenario(self) -> str:
        return self._scenario

    @scenario.setter
    def scenario(self, value: str):
        self._scenario = value
        self.rpc.scenario = value

    def open(self):
        self.connected = True
        return self

    def close(self):
        self.connected = False

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def cli(self, command: str) -> str:
        if "show version" in command:
            return f"Hostname: {self.name}\nModel: vJunos-router\nJunos: 23.2R1.14"
        if "show system uptime" in command:
            return f"Current time: 2026-10-15 17:00:00 UTC\nSystem booted: 2026-10-01 10:38:00 UTC\nUptime: 14 days"
        return f"Output for '{command}' on {self.name}"
# Interactive fault injection simulation
