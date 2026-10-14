# JunosNOC: Network Automation & Fault Detection

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Junos PyEZ](https://img.shields.io/badge/Junos%20PyEZ-2.8.2-orange.svg)](https://github.com/Juniper/py-junos-eznc)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests: Passing](https://img.shields.io/badge/Tests-12%20Passed-brightgreen.svg)]()

**JunosNOC** is an enterprise network automation, telemetry auditing, and fault detection platform built for Juniper Networks environments running **Junos OS**. Using **Junos PyEZ** and **NETCONF**, it continuously inspects operational RPCs, compares real-time routing engine states against engineering baselines, identifies network anomalies, and exports structured diagnostic reports.

---

## Key Highlights

- **Virtual Juniper Lab Architecture**: Complete 3-router enterprise network lab (`R1-CORE`, `R2-DIST`, `R3-EDGE`) featuring IPv4 transit addressing (`/30`), loopbacks (`/32`), static upstream routing, and multi-access OSPF Area 0 convergence.
- **PyEZ Operational RPC Telemetry**: Extracts interface packet statistics and error counters (`get_interface_information`), routing tables and protocol distributions (`get_route_information`), OSPF adjacency states and dead timers (`get_ospf_neighbor_information`), and RE health/CPU load (`get_system_uptime_information`).
- **Automated Fault Detection**: Continuous policy evaluation for operational interface downs, CRC/input errors, missing routing table prefixes, broken or flapping OSPF neighbor adjacencies, and CPU/memory threshold breaches.
- **Remediation & Recovery Verification**: Validates reachability using automated RPC ping matrices, interface bounce automation, and post-remediation verification loops.
- **Offline / Mock Mode**: Includes an offline Junos RPC adapter allowing full testing, demonstrations, and test execution without requiring heavy hypervisor VMs.

---

## Network Topology

```
                             +-----------------------+
                             |       ISP / WAN       |
                             |   198.51.100.1/30     |
                             +-----------+-----------+
                                         | ge-0/0/3.0
                                         v
                             +-----------------------+
                             |        R1-CORE        |
                             |  Router-ID: 10.0.0.1  |
                             |  Mgmt: 192.168.1.11   |
                             +-----------+-----------+
                            /                         \
        ge-0/0/0.0         /                           \  ge-0/0/1.0
   10.10.12.1/30          /                             \ 10.10.13.1/30
   (OSPF Area 0)         /                               \ (OSPF Area 0)
                        /                                 \
                       v                                   v
+-----------------------+                         +-----------------------+
|        R2-DIST        |       ge-0/0/1.0        |        R3-EDGE        |
|  Router-ID: 10.0.0.2  |-------------------------|  Router-ID: 10.0.0.3  |
|  Mgmt: 192.168.1.12   | 10.10.23.1/30 (Area 0)  |  Mgmt: 192.168.1.13   |
+-----------+-----------+                         +-----------+-----------+
            |                                                 |
            v                                                 v
    [ Branch-A LAN ]                                  [ Branch-B LAN ]
    192.168.20.0/24                                   192.168.30.0/24
```

See [topology/TOPOLOGY.md](topology/TOPOLOGY.md) for full interface, IP allocation, and routing details.

---

## Repository Structure

```
junos-noc/
├── .venv/                      # Python virtual environment
├── configs/                    # Junos configuration files
│   ├── r1_core.set             # Junos 'set' commands for R1
│   ├── r1_core.conf            # Junos hierarchical config for R1
│   ├── r2_dist.set             # Junos 'set' commands for R2
│   ├── r2_dist.conf            # Junos hierarchical config for R2
│   ├── r3_edge.set             # Junos 'set' commands for R3
│   ├── r3_edge.conf            # Junos hierarchical config for R3
│   └── lab_setup_eve_ng_gns3.md # Deployment guide for EVE-NG, GNS3 & Containerlab
├── inventory/
│   └── devices.yaml            # Device inventory, credentials & baseline expectations
├── rules/
│   └── baseline_rules.yaml     # Health thresholds, interface rules, and routing policies
├── topology/
│   ├── TOPOLOGY.md             # Detailed network topology & addressing specification
│   └── topology_diagram.txt    # ASCII topology diagram
├── junos_noc/
│   ├── __init__.py
│   ├── client.py               # PyEZ Device connection manager
│   ├── mock_device.py          # High-fidelity Junos RPC simulation adapter
│   ├── collectors/
│   │   ├── health.py           # RE CPU, memory, uptime, software version
│   │   ├── interfaces.py       # Interface status, IP assignments, Rx/Tx error counters
│   │   ├── routing.py          # Routing table (inet.0) & protocol distribution
│   │   └── ospf.py             # OSPF neighbor adjacencies, state & dead timers
│   ├── fault_detector.py       # Automated baseline anomaly detection engine
│   ├── reporter.py             # Rich console dashboard & JSON/Markdown report generator
│   └── troubleshoot.py         # Network ping matrix, interface bounce & recovery checks
├── reports/                    # Generated JSON and Markdown audit reports
├── tests/                      # Pytest automated test suite
├── REQUIREMENTS.md             # Detailed hardware & software requirements
├── requirements.txt            # Python dependencies
└── main.py                     # CLI entry point
```

---

## Quick Start

### 1. Setup Virtual Environment
```bash
# Clone the repository
git clone https://github.com/abhinxvz/junos-noc.git
cd junos-noc

# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1    # On Windows PowerShell
# source .venv/bin/activate     # On Linux / macOS

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Comprehensive Network Audit
Audit all network devices against configured baselines:
```bash
python main.py audit
```
*(Runs in offline simulation mode by default. Generates a rich terminal dashboard, saves structured diagnostic JSON in `reports/`, and produces a Markdown summary).*

### 3. Connect to Live Juniper Lab
To connect to live vJunos, vSRX, or physical Junos routers over NETCONF port 830:
```bash
python main.py audit --live
```

---

## CLI Operations and Incident Scenarios

### 1. Automated Fault Detection
Simulate and detect common network failure modes:
```bash
# Detect interface link down and CRC input errors
python main.py detect --scenario fault_interface

# Detect broken OSPF neighbor adjacency
python main.py detect --scenario fault_ospf

# Detect missing critical routing table prefix
python main.py detect --scenario fault_route

# Detect CPU load threshold breach
python main.py detect --scenario fault_cpu
```

### 2. End-to-End Connectivity Verification
Validates bidirectional ping reachability across all router loopbacks:
```bash
python main.py verify
```

### 3. Incident Simulation & Recovery Workflow
Demonstrates the full incident lifecycle: **Fault Injection** -> **Automated Detection** -> **Remediation Action** -> **Network Recovery Verification**:
```bash
python main.py simulate --fault fault_interface
```

---

## Running Unit Tests

The test suite tests all RPC collectors, fault rules, report generators, and troubleshooting actions:
```bash
pytest -v
```

Output:
```text
tests/test_collectors.py::test_health_collector PASSED                   [  8%]
tests/test_collectors.py::test_interface_collector PASSED                [ 16%]
tests/test_collectors.py::test_routing_collector PASSED                  [ 25%]
tests/test_collectors.py::test_ospf_collector PASSED                     [ 33%]
tests/test_fault_detector.py::test_healthy_network_no_faults PASSED      [ 41%]
tests/test_fault_detector.py::test_detect_interface_failure PASSED       [ 50%]
tests/test_fault_detector.py::test_detect_missing_route PASSED           [ 58%]
tests/test_fault_detector.py::test_detect_ospf_adjacency_down PASSED     [ 66%]
tests/test_reporter.py::test_save_json_and_markdown_reports PASSED       [ 75%]
tests/test_troubleshoot.py::test_ping_success PASSED                     [ 83%]
tests/test_troubleshoot.py::test_ping_failure_during_fault PASSED        [ 91%]
tests/test_troubleshoot.py::test_bounce_interface_recovers PASSED        [100%]
============================= 12 passed in 1.81s ==============================
```

---

## Sample Diagnostic JSON Report

When an audit is executed, a timestamped report is saved to `reports/`:
```json
{
  "timestamp": "2026-10-15 17:49:16 UTC",
  "devices": {
    "R1-CORE": {
      "health": {
        "hostname": "R1-CORE",
        "version": "23.2R1.14",
        "cpu_load_percent": 12.0,
        "memory_percent": 42.0
      },
      "interfaces": {
        "ge-0/0/0": {"admin_status": "up", "oper_status": "up", "speed": "1Gbps"},
        "ge-0/0/1": {"admin_status": "up", "oper_status": "up", "speed": "1Gbps"}
      },
      "ospf": {
        "total_neighbors": 2,
        "full_neighbors": 2,
        "all_full": true
      },
      "faults": []
    }
  }
}
```

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
