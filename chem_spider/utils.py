from abc import ABC
from typing import Dict, AnyStr, Callable, Optional

import aiohttp
import requests


def async_spider_retry(n_attempts):
    def outwrapper(func):
        async def wrapper(*args, **kwargs):
            for _ in range(n_attempts):
                res = await func(*args, **kwargs)
                if res["status"] == 200:
                    return res
            else:
                return res

        return wrapper
    return outwrapper


class BaseSpider(ABC):
    def __init__(self):
        self.pooling = {}

    @async_spider_retry(n_attempts=10)
    async def get(
            self,
            client: aiohttp.ClientSession,
            url: str,
            onSuccess,
            # onError,
            params: Optional[Dict] = None
    ):
        default_out = {
            "method": "get",
            "url": url,
            "status": -1,
            "out": None,
            "error": ""
        }

        try:

            proxy = await BaseSpider.get_proxy(client)
            if not proxy:
                default_out["error"] = "no unavailable proxy"
                return default_out

            self.pooling[proxy] = self.pooling.get(proxy, 0) + 1
            # await self.delete_proxy(client, proxy)

            async with client.get(url, params=params, proxy=f"http://{proxy}") as resp:
                if resp.status != 200:
                    default_out["status"] = resp.status
                    return default_out

                return {
                    "method": "get",
                    "url": url,
                    "status": resp.status,
                    "out": await onSuccess(resp)
                }

        except Exception as error:
            default_out["error"] = error
            return default_out

        # except aiohttp.ClientHttpProxyError as error:
        #     default_out["error"] = error
        #     return default_out
        #
        # except aiohttp.ServerDisconnectedError as error:
        #     default_out["error"] = error
        #     return default_out

    @staticmethod
    async def get_proxy(client: aiohttp.ClientSession):
        async with client.get("http://101.200.162.67:2203/get/") as resp:
            return (await resp.json()).get("proxy", "")

    @staticmethod
    async def delete_proxy(client, proxy):
        await client.get(f"http://101.200.162.67:2203/delete/?proxy={proxy}")

    @staticmethod
    async def dispose_str_response(response: aiohttp.ClientResponse):
        return await response.text()

    @staticmethod
    async def dispose_json_response(response: aiohttp.ClientResponse):
        return await response.json()
