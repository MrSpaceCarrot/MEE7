# Module Imports
import requests
from typing import Optional
from config import settings

# Send get request to api
def api_get(url: str, act_as_user: str = None) -> requests.Response:
    headers: dict = {'X-API-Key': settings.API_KEY}
    if act_as_user:
        headers["X-Act-As-User"] = str(act_as_user)
    return requests.get(url=f"{settings.API_BASE_URL}{url}", headers=headers)

# Send post request to api
def api_post(url: str, act_as_user: str = None, body: dict = None) -> requests.Response:
    headers: dict = {'X-API-Key': settings.API_KEY}
    if act_as_user:
        headers["X-Act-As-User"] = str(act_as_user)
    return requests.post(url=f"{settings.API_BASE_URL}{url}", headers=headers, json=body)
