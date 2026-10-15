"""
Device Health and System Information Collector.

Extracts device facts, Route Engine uptime, CPU load averages, and memory utilization
using Junos PyEZ facts and the `get_system_uptime_information` RPC.
"""

import re
import logging
from typing import Dict, Any, Union
from jnpr.junos import Device
from junos_noc.mock_device import MockDevice

logger = logging.getLogger("junos_noc.collectors.health")


class HealthCollector:
    """Collects system health, uptime, and hardware performance metrics from Junos devices."""

    def __init__(self, device: Union[Device, MockDevice]):
        self.device = device

    def collect(self) -> Dict[str, Any]:
        """
        Executes Junos RPCs and inspects facts to compile device health telemetry.

        :return: Standardized dictionary containing hardware, software, and utilization metrics.
        """
        facts = self.device.facts or {}
        hostname = facts.get("hostname", "Unknown")
        version = facts.get("version", "Unknown")
        model = facts.get("model", "Unknown")
        serial = facts.get("serialnumber", "Unknown")

        cpu_load = 0.0
        memory_percent = 0.0
        uptime_str = facts.get("uptime", "Unknown")
        uptime_hours = 0.0

        try:
            rpc_res = self.device.rpc.get_system_uptime_information()
            # Parse load average
            load_el = rpc_res.find(".//load-average-1")
            if load_el is not None and load_el.text:
                clean_load = load_el.text.replace("%", "").strip()
                try:
                    cpu_load = float(clean_load)
                except ValueError:
                    cpu_load = 0.0

            # Parse memory
            mem_el = rpc_res.find(".//memory-utilization")
            if mem_el is not None and mem_el.text:
                try:
                    memory_percent = float(mem_el.text.replace("%", "").strip())
                except ValueError:
                    memory_percent = 0.0

            # Parse uptime
            up_el = rpc_res.find(".//up-time")
            if up_el is not None and up_el.text:
                uptime_str = up_el.text.strip()
                uptime_hours = self._parse_uptime_to_hours(uptime_str)
        except Exception as e:
            logger.warning("Failed to parse get_system_uptime_information RPC for %s: %s", hostname, e)

        # Fallback to get_route_engine_information if metrics missing (common on physical MX/SRX/EX hardware)
        if cpu_load == 0.0 or memory_percent == 0.0:
            try:
                re_rpc = self.device.rpc.get_route_engine_information()
                re_el = re_rpc.find(".//route-engine")
                if re_el is not None:
                    if cpu_load == 0.0:
                        cpu_idle = re_el.findtext("cpu-idle")
                        if cpu_idle:
                            try:
                                cpu_load = round(100.0 - float(cpu_idle), 1)
                            except ValueError:
                                pass
                    if memory_percent == 0.0:
                        mem_buf = re_el.findtext("memory-buffer-utilization")
                        if mem_buf:
                            try:
                                memory_percent = float(mem_buf)
                            except ValueError:
                                pass
            except Exception:
                pass

        return {
            "hostname": hostname,
            "version": version,
            "model": model,
            "serial_number": serial,
            "uptime": uptime_str,
            "uptime_hours": uptime_hours,
            "cpu_load_percent": cpu_load,
            "memory_percent": memory_percent,
        }

    @staticmethod
    def _parse_uptime_to_hours(uptime_text: str) -> float:
        """Helper to convert Junos uptime strings (e.g., '14 days, 6 hours, 22 minutes') to hours."""
        total_hours = 0.0
        days_match = re.search(r"(\d+)\s+day", uptime_text)
        hours_match = re.search(r"(\d+)\s+hour", uptime_text)
        mins_match = re.search(r"(\d+)\s+minute", uptime_text)

        if days_match:
            total_hours += float(days_match.group(1)) * 24.0
        if hours_match:
            total_hours += float(hours_match.group(1))
        if mins_match:
            total_hours += float(mins_match.group(1)) / 60.0

        return round(total_hours, 2)
