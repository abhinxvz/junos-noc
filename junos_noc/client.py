"""
Junos Device Connection Manager.

Manages NETCONF connections via Junos PyEZ Device class, with transparent
fallback to MockDevice for offline development, interview demonstrations, and unit tests.
"""

import logging
from typing import Optional, Dict, Any, Union
from jnpr.junos import Device
from jnpr.junos.exception import ConnectAuthError, ConnectTimeoutError, ConnectError

from junos_noc.mock_device import MockDevice

logger = logging.getLogger("junos_noc.client")


class DeviceManager:
    """Factory and lifecycle manager for Junos PyEZ Device connections."""

    @staticmethod
    def get_device(
        host: str,
        user: str = "junos-admin",
        password: Optional[str] = None,
        port: int = 830,
        ssh_private_key_file: Optional[str] = None,
        timeout: int = 15,
        mock: bool = False,
        mock_scenario: str = "healthy",
        device_name: Optional[str] = None,
    ) -> Union[Device, MockDevice]:
        """
        Creates and returns an active connection to a Junos device.

        :param host: IP address or hostname of the router.
        :param user: NETCONF login username.
        :param password: Login password (or None if SSH key used).
        :param port: NETCONF port (default 830).
        :param ssh_private_key_file: Path to SSH private key if using key auth.
        :param timeout: Connection timeout in seconds.
        :param mock: If True, returns a MockDevice for offline simulation.
        :param mock_scenario: Scenario name for MockDevice ('healthy', 'fault_interface', etc.)
        :param device_name: Device identifier/hostname (used for mock data resolution).
        """
        resolved_name = device_name or host

        if mock:
            logger.info("Instantiating MockDevice for %s (scenario: %s)", resolved_name, mock_scenario)
            dev = MockDevice(
                host=host,
                user=user,
                name=resolved_name,
                scenario=mock_scenario,
            )
            dev.open()
            return dev

        dev_kwargs: Dict[str, Any] = {
            "host": host,
            "user": user,
            "port": port,
            "timeout": timeout,
            "gather_facts": True,
        }

        if password:
            dev_kwargs["passwd"] = password
        if ssh_private_key_file:
            dev_kwargs["ssh_private_key_file"] = ssh_private_key_file

        dev = Device(**dev_kwargs)

        try:
            logger.info("Connecting to %s (%s:%d) via NETCONF...", resolved_name, host, port)
            dev.open()
            logger.info("Successfully connected to %s (Junos %s)", resolved_name, dev.facts.get("version", "unknown"))
            return dev
        except ConnectAuthError as auth_err:
            logger.error("Authentication failed for %s: %s", host, auth_err)
            raise
        except ConnectTimeoutError as timeout_err:
            logger.error("Connection timed out connecting to %s:%d: %s", host, port, timeout_err)
            raise
        except ConnectError as conn_err:
            logger.error("Failed to establish NETCONF session to %s: %s", host, conn_err)
            raise
