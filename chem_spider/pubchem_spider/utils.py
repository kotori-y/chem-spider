import aiohttp


async def cid_to_smiles(client: aiohttp.ClientSession, cid: int) -> str:
