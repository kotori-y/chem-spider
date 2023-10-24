import warnings
from typing import List

import aiohttp

try:
    from ..utils import BaseSpider
except ImportError:
    from chem_spider.utils import BaseSpider

warnings.filterwarnings("ignore")


def _find_content_by_keywords(data, keyword):
    res = list(filter(lambda x: x["TOCHeading"] == keyword, data))
    if res:
        return res[0]["Section"]
    return []


class PubChemSpider(BaseSpider):
    def __init__(self):
        super().__init__()

    async def smiles_to_cids(self, smiles_array: List[str]):
        async with aiohttp.ClientSession() as client:
            task_list = []

            for smiles in smiles_array:
                url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/smiles/{smiles}/cids/TXT"
                task = asyncio.create_task(self.get(client, url, self.dispose_str_response))
                task_list.append(task)

            results = await asyncio.gather(*task_list)

            return [
                {
                    smiles_array[i]: res["out"].strip(),
                } for i, res in enumerate(results)
            ]

    async def cids_to_smiles(self, cid_list: List[int]):
        async with aiohttp.ClientSession() as client:
            task_list = []

            _cid_list = []
            for left in range(0, len(cid_list), 50):
                _cid_list.append(cid_list[left: left + 50])

            for _cids in _cid_list:
                cids = ",".join([str(x) for x in _cids])
                url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/" \
                      f"cid/{cids}/property/CanonicalSMILES,InChI,InChIKey/JSON"
                task = asyncio.create_task(self.get(client, url, self.dispose_json_response))
                task_list.append(task)

            results = await asyncio.gather(*task_list)

            out = []
            error = []

            for i, res in enumerate(results):
                if res["status"] != 200:
                    error.extend(_cid_list[i])
                    continue
                out.extend(res["out"]["PropertyTable"]["Properties"])

            return out, error

    async def cid_to_properties(self, cid: int, item_list: List[str]):
        def foobar(value):
            if "Number" in value:
                return [f"{value['Number'][0]} {value.get('Unit', '')}"]
            return [x["String"] for x in value["StringWithMarkup"]]

        async with aiohttp.ClientSession() as client:
            url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/{cid}/JSON/"
            data = await self.get(client, url, self.dispose_json_response)

            out = {"CID": cid}
            for item in item_list:
                out[item] = []

            if data["status"] != 200:
                return out

            cp_props = _find_content_by_keywords(data["out"]["Record"]["Section"], "Chemical and Physical Properties")
            if len(cp_props) <= 1:
                return out

            exp_props = _find_content_by_keywords(cp_props, "Experimental Properties")
            target_props = filter(lambda x: x["TOCHeading"] in item_list, exp_props)

            for target_prop in target_props:
                prop_name = target_prop["TOCHeading"]
                prop_value = sum([foobar(x["Value"]) for x in target_prop["Information"]], [])
                out[prop_name] = prop_value

            return out

    async def cids_to_properties(self, cid_list: List[int], items_list: List[str]):
        assert len(cid_list) <= 50

        task_list = [asyncio.create_task(self.cid_to_properties(cid, items_list)) for cid in cid_list]
        return await asyncio.gather(*task_list)


if __name__ == "__main__":
    import asyncio
    import pandas as pd

    endpoints = [
        "Odor",
        "Flash Point",
        "Boiling Point",
        "Density",
        "Vapor Pressure",
        "Heat of Combustion",
        "Melting Point",
        "Refractive Index",
        "Viscosity",
        "pH",
        "LogP",
        "LogS",
        "Solubility",
        "Henry's Law Constant",
        "Autoignition"
    ]

    spider = PubChemSpider()

    _cids = list(range(1, 100))
    ans = asyncio.run(spider.cids_to_properties(_cids + [2244], endpoints), debug=True)
    out = pd.DataFrame(ans)
    print(out)
