import httpx

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.session import ServerSession

from mcp.server.fastmcp import FastMCP
mcp = FastMCP(name="Resource Example")

@mcp.resource("file://documents/{name}")
def read_document(name: str) -> str:
    """Read a document by name."""
    # This would normally read from disk
    return f"Content of {name}"


@mcp.resource("config://settings")
def get_settings() -> str:
    """Get application settings."""
    return """{
  "theme": "dark",
  "language": "en",
  "debug": false
}"""

# Mock database class for example
class Database:
    """Mock database class for example."""

    @classmethod
    async def connect(cls) -> "Database":
        """Connect to database."""
        return cls()

    async def disconnect(self) -> None:
        """Disconnect from database."""
        pass

    def query(self) -> str:
        """Execute a query."""
        return "Query result"


@dataclass
class AppContext:
    """Application context with typed dependencies."""

    db: Database


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with type-safe context."""
    # Initialize on startup
    db = await Database.connect()
    try:
        yield AppContext(db=db)
    finally:
        # Cleanup on shutdown
        await db.disconnect()


# Pass lifespan to server
mcp = FastMCP("My App", lifespan=app_lifespan)


# Access type-safe lifespan context in tools
@mcp.tool()
def query_db(ctx: Context[ServerSession, AppContext]) -> str:
    """Tool that uses initialized resources."""
    db = ctx.request_context.lifespan_context.db
    return db.query()

# POKEAPI_BASE = "https://pokeapi.co/api/v2"

# # --- Helper to fetch Pokémon data ---
# async def fetch_pokemon_data(name: str) -> dict:
#     async with httpx.AsyncClient() as client:
#         try:
#             response = await client.get(f"{POKEAPI_BASE}/pokemon/{name.lower()}")
#             if response.status_code == 200:
#                 return response.json()
#         except httpx.HTTPError:
#             pass
#     return {}

# # --- Tool: Get info about a Pokémon ---
# @mcp.tool()
# async def get_pokemon_info(name: str) -> str:
#     """Get detailed info about a Pokémon by name."""
#     data = await fetch_pokemon_data(name)
#     if not data:
#         return f"No data found for Pokémon: {name}"

#     stats = {stat['stat']['name']: stat['base_stat'] for stat in data['stats']}
#     types_ = [t['type']['name'] for t in data['types']]
#     abilities = [a['ability']['name'] for a in data['abilities']]

#     return f"""
# Name: {data['name'].capitalize()}
# Types: {', '.join(types_)}
# Abilities: {', '.join(abilities)}
# Stats: {', '.join(f"{k}: {v}" for k, v in stats.items())}
# """

# # --- Tool: Create a tournament squad ---
# @mcp.tool()
# async def create_tournament_squad() -> str:
#     """Create a powerful squad of Pokémon for a tournament."""
#     top_pokemon = ["charizard", "garchomp", "lucario", "dragonite", "metagross", "gardevoir"]
#     squad = []

#     for name in top_pokemon:
#         data = await fetch_pokemon_data(name)
#         if data:
#             squad.append(data["name"].capitalize())

#     return "Tournament Squad:\n" + "\n".join(squad)

# # --- Tool: List popular Pokémon ---
# @mcp.tool()
# async def list_popular_pokemon() -> str:
#     """List popular tournament-ready Pokémon."""
#     return "\n".join([
#         "Charizard", "Garchomp", "Lucario",
#         "Dragonite", "Metagross", "Gardevoir"
#     ])

# # --- Entry point ---
# if __name__ == "__main__":
#     mcp.run(transport="stdio")