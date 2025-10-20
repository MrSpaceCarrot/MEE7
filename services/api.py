# Module Imports
from config import settings
from bot import client


# Send get request to any url
async def get_request(url: str) -> dict:
    async with client.session.get(url=url) as response:
        content = await response.json()
        return {"status": response.status,
                "ok": response.ok,
                "content": content}


# Send get request to api
async def api_get(url: str, act_as_user: str = None) -> dict:
    headers: dict = {'X-API-Key': settings.API_KEY}
    if act_as_user:
        headers["X-Act-As-User"] = str(act_as_user)

    async with client.session.get(url=f"{settings.API_BASE_URL}{url}", headers=headers) as response:
        content = await response.json()
        return {"status": response.status,
                "ok": response.ok,
                "content": content}
            

# Send post request to api
async def api_post(url: str, act_as_user: str = None, body: dict = None) -> dict:
    headers: dict = {'X-API-Key': settings.API_KEY}
    if act_as_user:
        headers["X-Act-As-User"] = str(act_as_user)

    async with client.session.post(url=f"{settings.API_BASE_URL}{url}", headers=headers, json=body) as response:
        content = await response.json()
        return {"status": response.status,
                "ok": response.ok,
                "content": content}
