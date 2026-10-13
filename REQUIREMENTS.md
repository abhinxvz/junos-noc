# JunosNOC: Project Requirements & Prerequisites

This document outlines everything required to deploy, execute, and evaluate the **JunosNOC** Network Automation and Fault Detection project.

---

## 1. Fast Track: Running on Desktop (No Hypervisor Required)

You do **NOT** need to spin up heavy router VMs to run, test, and demonstrate this project on your desktop. The project comes equipped with a high-fidelity **Mock Junos Telemetry Adapter** that implements all Junos PyEZ RPCs (`get_route_information`, `get_interface_information`, `get_ospf_neighbor_information`, `get_system_uptime_information`, and `ping`).

### Software & Environment:
- **Operating System**: Windows 10/11, macOS, or Linux.
- **Python**: Python 3.9 or higher (tested on Python 3.12).
- **RAM**: ~100 MB RAM for Python runtime.
- **Dependencies**:
  - `junos-eznc` (Junos PyEZ)
  - `ncclient` (NETCONF Python client)
  - `paramiko` (SSH transport)
  - `lxml` (XML RPC parser)
  - `PyYAML` (Inventory & baseline rules)
  - `rich` (Terminal dashboards and colored tables)
  - `pytest` (Unit and integration test suite)

---

## 2. Live Virtual Network Lab Requirements (Optional for Full Emulation)

If you wish to spin up the actual 3-router Juniper network lab in a virtualized hypervisor environment, the following components are required:

### A. Virtualization Platform (Choose One)
1. **EVE-NG (Community or Professional)**:
   - Recommended platform for multi-vendor network topology simulation.
   - Runs in VMware Workstation (Windows) or bare metal Linux.
2. **GNS3**:
   - Free, open-source network emulator with GNS3 VM.
3. **Containerlab with vrnetlab**:
   - Modern Docker/KVM container-based lab environment on Linux / WSL2.

### B. Juniper Virtual Router Appliances (Junos OS)
To deploy 3 virtual routers (`R1-CORE`, `R2-DIST`, `R3-EDGE`), obtain one of the following official images from Juniper Networks:
- **vJunos-router (or vJunos-switch)**:
  - Format: QCOW2 image (`vjunosrouter-23.2R1.14.qcow2`).
  - Resources: **4 GB RAM and 2 vCPUs per router** (Total: 12 GB RAM, 6 vCPUs).
- **vSRX (vSRX 3.0)**:
  - Format: QCOW2 or OVA.
  - Resources: **4 GB RAM and 2 vCPUs per router**.
  - Note: Run `set security forwarding-options family inet mode packet-based` for pure router behavior.
- **vMX**:
  - Requires Control Plane (VCP) and Forwarding Plane (VFP) VMs.
  - Resources: **8 GB RAM per router** (Total: ~24 GB RAM).

### C. Host Machine Hardware for 3 Live VMs
- **CPU**: Intel Core i7 / AMD Ryzen 7 (with Intel VT-x / AMD-V enabled in BIOS).
- **RAM**: Minimum 16 GB RAM (32 GB recommended if running EVE-NG VM alongside browser and IDE).
- **Disk**: 40 GB+ free SSD storage.

---

## 3. Junos Configuration Prerequisites (For Live Devices)

Each router in the lab must have the following configuration applied to allow Junos PyEZ to communicate over NETCONF:

1. **System Services**:
   ```junos
   set system services ssh root-login allow
   set system services ssh protocol-version v2
   set system services netconf ssh
   ```

2. **NOC Automation User**:
   ```junos
   set system login user junos-admin class super-user authentication plain-text-password-value "Juniper123!"
   ```

3. **Management Network & Port Reachability**:
   - Out-of-band management interface configured (e.g. `fxp0.0` or `em0.0`):
     - `R1-CORE`: `192.168.1.11/24`
     - `R2-DIST`: `192.168.1.12/24`
     - `R3-EDGE`: `192.168.1.13/24`
   - TCP Port **830** (NETCONF subsystem) and TCP Port **22** (SSH) must be open and reachable from your workstation.

---

## 4. Summary Checklist

| Requirement | Desktop / Mock Mode | Live Lab Mode (EVE-NG / GNS3) |
| :--- | :---: | :---: |
| Python 3.10+ | Required | Required |
| `junos-eznc` package | Required | Required |
| `rich`, `pytest`, `pyyaml` | Required | Required |
| Hypervisor (VMware / KVM) | Not needed | Required |
| Junos QCOW2 Images | Not needed | Required |
| 16 GB+ Host RAM | Not needed | Required |
| NETCONF Port 830 open | Not needed | Required |
