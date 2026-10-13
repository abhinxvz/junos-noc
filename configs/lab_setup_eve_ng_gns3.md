# Junos Virtual Lab Deployment Guide (EVE-NG / GNS3 / Containerlab)

This guide provides step-by-step instructions for deploying the 3-router Junos virtual lab in hypervisor and network simulation environments.

---

## 1. Supported Junos Images

You can use any of the following Juniper virtual machine appliances:
- **vJunos-router / vJunos-switch**: Modern KVM-native image (recommended, ~4 GB RAM per node).
- **vSRX (vSRX 3.0)**: Firewall appliance operating in packet-based forwarding mode (~4 GB RAM per node).
- **vMX**: Virtual MX router (Control Plane VCP + Forwarding Plane VFP, ~8 GB RAM per node).

---

## 2. Hardware Requirements for Live Virtual Lab

| Topology Nodes | Recommended RAM | Recommended vCPUs | Disk Space |
| :--- | :--- | :--- | :--- |
| **3x vJunos-router** | 12 GB RAM | 6 vCPUs (2 per VM) | 40 GB SSD |
| **3x vSRX 3.0** | 12 - 16 GB RAM | 6 vCPUs | 50 GB SSD |
| **Host System** | 16 GB+ RAM | Intel VT-x / AMD-V enabled | Windows 10/11 with WSL2 or dedicated Linux server |

> **Note**: If your computer does not have enough RAM to run three concurrent virtual routers, use the **JunosNOC Mock Mode (`--mock`)**. The automation suite, fault detection engine, and diagnostic reporting run with 100% fidelity offline without spinning up hypervisors!

---

## 3. Deploying in EVE-NG

1. Upload the Junos image into `/opt/unetlab/addons/qemu/` (e.g. `vjunosrouter-23.2R1.14/virtioa.qcow2`).
2. Run `/opt/unetlab/wrappers/unl_wrapper -a fixpermissions`.
3. In EVE-NG Web UI:
   - Create a new lab: `Junos-NOC-Enterprise`.
   - Add three Junos nodes: `R1-CORE`, `R2-DIST`, `R3-EDGE`.
   - Connect the interfaces according to `topology/TOPOLOGY.md`:
     - `R1 ge-0/0/0` <---> `R2 ge-0/0/0`
     - `R1 ge-0/0/1` <---> `R3 ge-0/0/0`
     - `R2 ge-0/0/1` <---> `R3 ge-0/0/1`
     - Connect `fxp0` on all routers to the `Management Cloud / Cloud0` bridge.
4. Start the nodes and open the VNC/Telnet consoles.
5. In each router console:
   ```junos
   cli
   configure
   # Paste contents of configs/r1_core.set (or r2_dist.set / r3_edge.set)
   commit and-quit
   ```

---

## 4. Deploying in GNS3

1. Import the Junos appliance from the GNS3 Appliance Registry (`vJunos` or `vSRX`).
2. Add an Ethernet Switch or Cloud node mapped to your host loopback adapter (`192.168.1.0/24`).
3. Connect `fxp0` on R1, R2, R3 to the Management Cloud.
4. Connect the inter-router transit links (`ge-0/0/0`, `ge-0/0/1`).
5. Boot all nodes and load the `.set` configuration files.

---

## 5. Deploying with Containerlab & vrnetlab

If running in Linux/WSL2 with Docker:
```yaml
name: junos-noc-lab
topology:
  nodes:
    r1:
      kind: vr-juniper_vjunosrouter
      image: vrnetlab/vr-vjunosrouter:23.2R1.14
      mgmt-ipv4: 192.168.1.11
    r2:
      kind: vr-juniper_vjunosrouter
      image: vrnetlab/vr-vjunosrouter:23.2R1.14
      mgmt-ipv4: 192.168.1.12
    r3:
      kind: vr-juniper_vjunosrouter
      image: vrnetlab/vr-vjunosrouter:23.2R1.14
      mgmt-ipv4: 192.168.1.13
  links:
    - endpoints: ["r1:eth1", "r2:eth1"]
    - endpoints: ["r1:eth2", "r3:eth1"]
    - endpoints: ["r2:eth2", "r3:eth2"]
```
Deploy via:
```bash
sudo containerlab deploy -t topology.clab.yml
```

---

## 6. Verifying NETCONF & SSH Access

From your workstation terminal:
```bash
# Test SSH
ssh junos-admin@192.168.1.11

# Test NETCONF port 830
Test-NetConnection -ComputerName 192.168.1.11 -Port 830
```
Once reachable, you can execute the Python automation tool directly against your live lab!

<!-- Hypervisor Deployment Notes: October 2026 -->
