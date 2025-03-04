from datetime import datetime
from typing import Any, Dict

import httpx
from mcp.server.fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("entur-departures", dependencies=["httpx", "mcp"])

# Constants
ENTUR_API_URL = "https://api.entur.io/journey-planner/v3/graphql"
CLIENT_NAME = "entur-mcp-server"

# GraphQL queries
# Using a different approach for searching stops
STOP_SEARCH_QUERY = """
query($query: String!, $limit: Int!) {
  stopPlaces(ids: [], name: $query, limit: $limit) {
    id
    name
    transportMode
    latitude
    longitude
  }
}
"""

DEPARTURES_QUERY = """
query($id: String!, $numberOfDepartures: Int!) {
  stopPlace(id: $id) {
    id
    name
    estimatedCalls(numberOfDepartures: $numberOfDepartures) {
      realtime
      aimedDepartureTime
      expectedDepartureTime
      destinationDisplay {
        frontText
      }
      serviceJourney {
        journeyPattern {
          line {
            id
            publicCode
            transportMode
          }
        }
      }
    }
  }
}
"""


# Helper functions
async def fetch_from_entur(query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
    """Make a request to the Entur API"""
    headers = {"ET-Client-Name": CLIENT_NAME}
    request = {"query": query, "variables": variables}

    async with httpx.AsyncClient() as client:
        response = await client.post(
            ENTUR_API_URL, json=request, headers=headers, timeout=15.0
        )
        response.raise_for_status()
        result = response.json()

        # Debug logging
        if "errors" in result:
            print(f"API Error: {result['errors']}")
            print(f"Query: {query}")
            print(f"Variables: {variables}")

        return result


def format_time(time_str: str) -> str:
    """Format time string to a more readable format"""
    dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
    local_time = dt.astimezone()
    return local_time.strftime("%H:%M")


def calculate_delay(expected: str, aimed: str) -> int:
    """Calculate delay in minutes between expected and aimed time"""
    expected_dt = datetime.fromisoformat(expected.replace("Z", "+00:00"))
    aimed_dt = datetime.fromisoformat(aimed.replace("Z", "+00:00"))
    delay_seconds = (expected_dt - aimed_dt).total_seconds()
    return round(delay_seconds / 60)


# Fall back approach if the GraphQL queries don't work
async def fallback_stop_search(query: str, limit: int = 5) -> Dict[str, Any]:
    """
    Use Entur's geocoder API as fallback for stop search
    """
    geocoder_url = f"https://api.entur.io/geocoder/v1/autocomplete?text={query}&size={limit}&layers=venue&multiModal=true"
    headers = {"ET-Client-Name": CLIENT_NAME}

    async with httpx.AsyncClient() as client:
        response = await client.get(geocoder_url, headers=headers, timeout=15.0)
        response.raise_for_status()
        result = response.json()

        stops = []
        for feature in result.get("features", []):
            properties = feature.get("properties", {})
            if properties.get("layer") == "venue" and properties.get(
                "id", ""
            ).startswith("NSR:StopPlace:"):
                stops.append(
                    {
                        "id": properties.get("id"),
                        "name": properties.get("name"),
                        "latitude": feature.get("geometry", {}).get(
                            "coordinates", [0, 0]
                        )[1],
                        "longitude": feature.get("geometry", {}).get(
                            "coordinates", [0, 0]
                        )[0],
                    }
                )

        return {"data": {"stops": stops}}


# MCP Tools
@mcp.tool()
async def search_stops(query: str, limit: int = 5) -> str:
    """
    Search for stops by name

    Args:
        query: Search string for finding stops
        limit: Maximum number of results to return
    """
    try:
        # Try GraphQL approach first
        try:
            result = await fetch_from_entur(
                STOP_SEARCH_QUERY, {"query": query, "limit": limit}
            )

            if "errors" in result:
                # Fall back to geocoder API
                result = await fallback_stop_search(query, limit)
                stops = result.get("data", {}).get("stops", [])
            else:
                stops = result.get("data", {}).get("stopPlaces", [])
        except Exception:
            # Fall back to geocoder API on any error
            result = await fallback_stop_search(query, limit)
            stops = result.get("data", {}).get("stops", [])

        if not stops:
            return f"No stops found matching '{query}'"

        response = ["Found these stops:"]
        for stop in stops:
            response.append(f"• {stop['name']} (ID: {stop['id']})")

        return "\n".join(response)
    except Exception as e:
        return f"Error searching for stops: {str(e)}"


@mcp.tool()
async def get_departures(stop_id: str, num_departures: int = 5) -> str:
    """
    Get upcoming departures from a stop

    Args:
        stop_id: The ID of the stop (NSR:StopPlace:XXXXX)
        num_departures: Number of departures to return
    """
    if not stop_id.startswith("NSR:StopPlace:"):
        return "Invalid stop ID format. Stop IDs should begin with 'NSR:StopPlace:'"

    try:
        result = await fetch_from_entur(
            DEPARTURES_QUERY, {"id": stop_id, "numberOfDepartures": num_departures}
        )

        if "errors" in result:
            return f"Error getting departures: {result['errors'][0]['message']}"

        stop_data = result.get("data", {}).get("stopPlace", {})

        if not stop_data:
            return f"Stop with ID {stop_id} not found"

        stop_name = stop_data.get("name", "Unknown stop")
        calls = stop_data.get("estimatedCalls", [])

        if not calls:
            return f"No departures found for {stop_name} in the near future"

        response = [f"Departures from {stop_name}:"]

        for call in calls:
            line = call["serviceJourney"]["journeyPattern"]["line"]["publicCode"]
            destination = call["destinationDisplay"]["frontText"]
            transport_mode = call["serviceJourney"]["journeyPattern"]["line"][
                "transportMode"
            ].lower()

            aimed_time = format_time(call["aimedDepartureTime"])
            expected_time = format_time(call["expectedDepartureTime"])

            delay = calculate_delay(
                call["expectedDepartureTime"], call["aimedDepartureTime"]
            )

            status = "on time"
            if delay > 0:
                status = f"{delay} min late"
            elif delay < 0:
                status = f"{abs(delay)} min early"

            response.append(
                f"• {line} {destination} ({transport_mode}): {expected_time} ({status})"
            )

        return "\n".join(response)
    except Exception as e:
        return f"Error getting departures: {str(e)}"


@mcp.tool()
async def get_departures_by_name(stop_name: str, num_departures: int = 5) -> str:
    """
    Find a stop by name and get upcoming departures

    Args:
        stop_name: Name of the stop to search for
        num_departures: Number of departures to return
    """
    try:
        # First search for the stop using our fallback method
        search_result = await fallback_stop_search(stop_name, 1)

        stops = search_result.get("data", {}).get("stops", [])

        if not stops:
            return f"No stops found matching '{stop_name}'"

        # Use the first result
        stop = stops[0]
        stop_id = stop["id"]

        # Now get departures for this stop
        return await get_departures(stop_id, num_departures)
    except Exception as e:
        return f"Error getting departures: {str(e)}"


# Run the server if executed directly
if __name__ == "__main__":
    mcp.run()
