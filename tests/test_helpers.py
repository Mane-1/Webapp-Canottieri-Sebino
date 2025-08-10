from httpx import AsyncClient


async def login(client: AsyncClient, username: str, password: str):
    return await client.post("/login", data={"username": username, "password": password})
