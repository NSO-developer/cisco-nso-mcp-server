#!/usr/bin/env python3
"""
Cisco NSO MCP Server

This module implements a Model Context Protocol (MCP) server that provides
network automation tools for interacting with Cisco NSO via RESTCONF.
"""
import argparse
import os
from typing import Any, Dict, Optional
from cisco_nso_mcp_server.services.devices import (
    get_device_config,
    get_device_ned_ids,
    get_device_platform,
    get_device_state,
    check_device_sync,
    sync_from_device,
    get_device_groups
)
from cisco_nso_mcp_server.services.services import (
    get_service_types,
    get_services
)
from cisco_nso_mcp_server.services.environment import get_environment_summary
from cisco_nso_mcp_server.utils import logger
from cisco_nso_restconf.client import NSORestconfClient
from cisco_nso_restconf.devices import Devices
from cisco_nso_restconf.query import Query
from fastmcp import FastMCP
from starlette.responses import JSONResponse


def register_resources(mcp: FastMCP, devices_helper: Devices, query_helper: Query) -> None:
    """
    Register resources with the MCP server.

    This function registers all available resources with the MCP server,
    including the NSO environment summary resource that provides information
    about the network devices managed by NSO.

    Args:
        mcp: The FastMCP server instance to register resources with
        query_helper: The Query helper for interacting with NSO
        devices_helper: The Devices helper for interacting with NSO devices
    """
    @mcp.resource(
        uri="https://resources.cisco-nso-mcp.io/environment",
        description="NSO environment summary",
    )
    async def nso_environment() -> Dict[str, Any]:
        """
        This resource provides a summary of the NSO environment, including
        the number of devices managed by NSO, the distribution of operating
        systems, the number of device groups, and the distribution of device
        models.

        Returns:
            A dictionary containing summary information about the NSO
            environment.
        """
        try:
            # delegate to the service layer
            return await get_environment_summary(query_helper, devices_helper)

        except Exception as e:
            logger.error(f"Resource error: {str(e)}")

            return {
                "status": "error",
                "error_message": str(e)
            }

def register_tools(mcp: FastMCP, client: NSORestconfClient, devices_helper: Devices) -> None:
    """
    Register tools with the MCP server.

    This function registers all available tools with the MCP server,
    including tools for retrieving device platform information, device configuration,
    Network Element Driver (NED) IDs, and services from Cisco NSO.

    Args:
        mcp: The FastMCP server instance to register tools with
        client: The NSORestconfClient instance for interacting with NSO
        devices_helper: The Devices helper for interacting with NSO devices
    """
    @mcp.tool(
        name="get_service_types",
        description="Retrieve the available service types in Cisco NSO.",
        tags={"services", "types"},
        annotations={
            "title": "Get Service Types",
            "readOnlyHint": True
        }
    )
    async def get_service_types_tool(params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        This tool retrieves the available service types in Cisco NSO.
        The response will include a list of available service types.

        Args:
            params (Optional[Dict[str, Any]], optional): Unused parameter. Defaults to None.

        Returns:
            A dictionary containing a list of available service types.
        """
        try:
            # delegate to the service layer
            return await get_service_types(client)

        except Exception as e:
            return {
                "status": "error",
                "error_message": str(e)
            }

    @mcp.tool(
        name="get_services",
        description="Retrieve the available services in Cisco NSO. Requires a 'service_type' parameter.",
        tags={"services", "service"},
        annotations={
            "title": "Get Services",
            "readOnlyHint": True
        }
    )
    async def get_services_tool(params: Dict[str, Any]) -> Dict[str, Any]:
        """
        This tool retrieves the available services in Cisco NSO.
        The response will include a list of available services.

        Args:
            params (Optional[Dict[str, Any]], optional): Unused parameter. Defaults to None.

        Returns:
            A dictionary containing a list of available services.
        """
        try:
            # validate required parameters
            if not params or "service_type" not in params:
                return {
                    "status": "error",
                    "error_message": "Missing required parameter: service_type"
                }

            # delegate to the service layer
            return await get_services(client, params["service_type"])

        except Exception as e:
            return {
                "status": "error",
                "error_message": str(e)
            }

    @mcp.tool(
        name="get_device_platform",
        description="Retrieve platform information for a specific device in Cisco NSO. Requires a 'device_name' parameter.",
        tags={"devices", "platform"},
        annotations={
            "title": "Get Device Platform Information",
            "readOnlyHint": True
        }
    )
    async def get_device_platform_tool(params: Dict[str, Any]) -> Dict[str, Any]:
        """
        This tool takes a single parameter, 'device_name', which is the name of
        the device for which to retrieve platform information. The response will
        include the platform name, platform version, and model information for
        the specified device.

        Args:
            params (Dict[str, Any]): A dictionary containing the 'device_name'
                parameter.

        Returns:
            A dictionary containing the platform information for the specified
            device.
        """
        try:
            # validate required parameters
            if not params or "device_name" not in params:
                return {
                    "status": "error",
                    "error_message": "Missing required parameter: device_name"
                }

            # delegate to the service layer
            return await get_device_platform(devices_helper, params["device_name"])

        except Exception as e:
            return {
                "status": "error",
                "error_message": str(e)
            }

    @mcp.tool(
        name="get_device_config",
        description="Retrieve the full configuration for a specific device in Cisco NSO. Requires a 'device_name' parameter.",
        tags={"devices", "config"},
        annotations={
            "title": "Get Device Configuration",
            "readOnlyHint": True
        }
    )
    async def get_device_config_tool(params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # validate required parameters
            if not params or "device_name" not in params:
                return {
                    "status": "error",
                    "error_message": "Missing required parameter: device_name"
                }

            # delegate to the service layer
            return await get_device_config(devices_helper, params["device_name"])

        except Exception as e:
            return {
                "status": "error",
                "error_message": str(e)
            }

    @mcp.tool(
        name="get_device_state",
        description="Retrieve the state for a specific device in Cisco NSO. Requires a 'device_name' parameter.",
        tags={"devices", "state"},
        annotations={
            "title": "Get Device State",
            "readOnlyHint": True
        }
    )
    async def get_device_state_tool(params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # validate required parameters
            if not params or "device_name" not in params:
                return {
                    "status": "error",
                    "error_message": "Missing required parameter: device_name"
                }

            # delegate to the service layer
            return await get_device_state(devices_helper, params["device_name"])

        except Exception as e:
            return {
                "status": "error",
                "error_message": str(e)
            }

    @mcp.tool(
        name="get_device_groups",
        description="Retrieve the available device groups in Cisco NSO.",
        tags={"devices", "groups"},
        annotations={
            "title": "Get Device Groups",
            "readOnlyHint": True
        }
    )
    async def get_device_groups_tool(params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        This tool retrieves the available device groups in Cisco NSO. The response will include a list of available device groups.

        Args:
            params (Optional[Dict[str, Any]], optional): Unused parameter. Defaults to None.

        Returns:
            A dictionary containing a list of available device groups.
        """
        try:
            # delegate to the service layer
            return await get_device_groups(devices_helper)

        except Exception as e:
            return {
                "status": "error",
                "error_message": str(e)
            }

    @mcp.tool(
        name="get_device_ned_ids",
        description="Retrieve the available Network Element Driver (NED) IDs in Cisco NSO.",
        tags={"devices", "neds"},
        annotations={
            "title": "Get Device NED ID's",
            "readOnlyHint": True
        }
    )
    async def get_device_ned_ids_tool(params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        This tool retrieves the available Network Element Driver (NED) IDs in
        Cisco NSO. The response will include a list of available NED IDs.

        Args:
            params (Optional[Dict[str, Any]], optional): Unused parameter. Defaults to None.

        Returns:
            A dictionary containing a list of available NED IDs.
        """
        try:
            # delegate to the service layer
            return await get_device_ned_ids(devices_helper)

        except Exception as e:
            return {
                "status": "error",
                "error_message": str(e)
            }

    @mcp.tool(
        name="check_device_sync",
        description="Check the sync status for a specific device in Cisco NSO. Requires a 'device_name' parameter.",
        tags={"devices", "sync"},
        annotations={
            "title": "Check Device Sync Status",
            "readOnlyHint": True
        }
    )
    async def check_device_sync_tool(params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # validate required parameters
            if not params or "device_name" not in params:
                return {
                    "status": "error",
                    "error_message": "Missing required parameter: device_name"
                }

            # delegate to the service layer
            return await check_device_sync(devices_helper, params["device_name"])

        except Exception as e:
            return {
                "status": "error",
                "error_message": str(e)
            }

    @mcp.tool(
        name="sync_from_device",
        description="Sync from a specific device in Cisco NSO. Requires a 'device_name' parameter.",
        tags={"devices", "sync"},
        annotations={
            "title": "Sync Device",
            "readOnlyHint": False
        }
    )
    async def sync_from_device_tool(params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # validate required parameters
            if not params or "device_name" not in params:
                return {
                    "status": "error",
                    "error_message": "Missing required parameter: device_name"
                }

            # delegate to the service layer
            return await sync_from_device(devices_helper, params["device_name"])

        except Exception as e:
            return {
                "status": "error",
                "error_message": str(e)
            }

def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments for the Cisco NSO MCP Server.

    This function parses the command line arguments and returns a Namespace object
    containing the parsed values.

    The following options are available:

    NSO Connection Options:
        --nso-scheme: NSO connection scheme (default: http)
        --nso-address: NSO server address (default: localhost)
        --nso-port: NSO server port (default: 8080)
        --nso-timeout: NSO connection timeout in seconds (default: 10)
        --nso-username: NSO username (default: admin)
        --nso-password: NSO password (default: admin)

    MCP Server Options:
        --transport: MCP transport type (default: stdio)
            Choices: stdio, http

    HTTP Transport Options (only used when --transport=http):
        --host: Host to bind to when using HTTP transport (default: 0.0.0.0)
        --port: Port to bind to when using HTTP transport (default: 8000)

    Returns:
        A Namespace object containing the parsed values.
    """
    parser = argparse.ArgumentParser(description="Cisco NSO MCP Server")

    # NSO connection parameters
    nso_group = parser.add_argument_group('NSO Connection Options')
    nso_group.add_argument(
        "--nso-scheme",
        default=os.environ.get("NSO_SCHEME", "http"),
        help="NSO connection scheme (default: http)"
    )
    nso_group.add_argument(
        "--nso-address",
        default=os.environ.get("NSO_ADDRESS", "localhost"),
        help="NSO server address (default: localhost)"
    )
    nso_group.add_argument(
        "--nso-port",
        type=int,
        default=int(os.environ.get("NSO_PORT", "8080")),
        help="NSO server port (default: 8080)"
    )
    nso_group.add_argument(
        "--nso-timeout",
        type=int,
        default=int(os.environ.get("NSO_TIMEOUT", "10")),
        help="NSO connection timeout in seconds (default: 10)"
    )
    nso_group.add_argument(
        "--nso-username",
        default=os.environ.get("NSO_USERNAME", "admin"),
        help="NSO username (default: admin)"
    )
    nso_group.add_argument(
        "--nso-password",
        default=os.environ.get("NSO_PASSWORD", "admin"),
        help="NSO password (default: admin)"
    )
    nso_group.add_argument(
        "--nso-verify",
        default=os.environ.get("NSO_VERIFY", True),
        action=argparse.BooleanOptionalAction,
        help="Verify NSO HTTPS certificate (default: True). Use --no-nso-verify for self-signed certs (dev only).",
    )
    nso_group.add_argument(
        "--nso-ca-bundle",
        default=os.environ.get("NSO_CA_BUNDLE"),
        help="Path to a CA bundle file to trust for NSO HTTPS.",
    )

    # MCP server parameters
    mcp_group = parser.add_argument_group('MCP Server Options')
    mcp_group.add_argument(
        "--transport",
        default=os.environ.get("MCP_TRANSPORT", "stdio"),
        choices=["stdio", "http"],
        help="MCP transport type (default: stdio)"
    )

    # HTTP-specific parameters
    http_group = parser.add_argument_group('HTTP Transport Options (only used when --transport=http)')
    http_group.add_argument(
        "--host",
        default=os.environ.get("MCP_HOST", "0.0.0.0"),
        help="Host to bind to when using HTTP transport (default: 0.0.0.0)"
    )
    http_group.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("MCP_PORT", "8000")),
        help="Port to bind to when using HTTP transport (default: 8000)"
    )

    args = parser.parse_args()

    return args

def main():
    """
    Main function to run the server.
    """

    # parse command line arguments
    args = parse_args()

    # initialize FastMCP server
    mcp = FastMCP(name="nso-mcp")

    # initialize NSO client with configurable parameters
    client = NSORestconfClient(
        scheme=args.nso_scheme,
        address=args.nso_address,
        port=args.nso_port,
        timeout=args.nso_timeout,
        username=args.nso_username,
        password=args.nso_password,
        disable_warning=(getattr(args, "nso_scheme", "http") == "https" and not getattr(args, "nso_verify", True)),
    )

    # cisco-nso-restconf uses requests.Session internally. Configure TLS verification
    # at the session layer so --no-nso-verify actually disables cert checks.
    if getattr(args, "nso_scheme", "http") == "https":
        if getattr(args, "nso_ca_bundle", None):
            client.session.verify = args.nso_ca_bundle
        else:
            client.session.verify = getattr(args, "nso_verify", True)

    logger.info("NSORestconfClient initialized")

    # initialize NSO client helpers
    devices_helper = Devices(client) # devices helper
    query_helper = Query(client) # query helper

	# implement health check endpoint (http://<ip:<port>/health)
    @mcp.custom_route("/health", methods=["GET"])
    async def health_check(request):
        return JSONResponse({"status": "healthy", "service": "mcp-server"})

    # register resources and tools
    register_resources(mcp, devices_helper, query_helper) # register resources
    register_tools(mcp, client, devices_helper) # register tools

    # run the server with stdio transport
    if args.transport == "stdio":
        logger.info("🚀 Starting Model Context Protocol (MCP) NSO Server with stdio transport")
        mcp.run(transport="stdio")

    # run the server with HTTP transport
    elif args.transport == "http":
        logger.info(f"🚀 Starting Model Context Protocol (MCP) NSO Server with HTTP transport on {args.host}:{args.port}")
        mcp.run(transport="http", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
