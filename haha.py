import httpx
import asyncio
import random
import json
from urllib.parse import quote, urlencode
from time import time
from pydantic import BaseModel
from typing import Optional
import pandas as pd
from env import SCRAPEOPS_API_KEY, SCRAPINGANT_API_KEY, PROXYSCRAPE_API_KEY

SCRAPINGANT_BASE_URL = "https://api.scrapingant.com/v2/general"
SCRAPEOPS_ENDPOINT = 'https://headers.scrapeops.io/v1/browser-headers'
PRODUCT = "ear pods"


def build_scrapingant_url(page):
    target_url = f"https://www.daraz.pk/catalog/?ajax=true&isFirstRequest=true&page={page}&q={quote(PRODUCT)}&spm=a2a0e.tm80335142.search.d_go"
    params = {
        'url': target_url,
        'x-api-key': SCRAPINGANT_API_KEY,
        'browser': 'false'
    }
    scrapingant_url = f"{SCRAPINGANT_BASE_URL}?{urlencode(params)}"
    return scrapingant_url


async def get_scrapeops_headers():
    async with httpx.AsyncClient() as client:
        params = {'api_key': SCRAPEOPS_API_KEY, 'num_results': 50}
        response = await client.get(SCRAPEOPS_ENDPOINT, params=params)
        return response.json().get("result", [])


def get_proxyscrape_proxies_local(file_path="proxyscrape_premium_http_proxies.txt"):
    try:
        with open(file_path, "r") as f:
            proxies = [line.strip() for line in f if line.strip()]
        print(f"✅ Loaded {len(proxies)} proxies from local file.")
        return proxies
    except Exception as e:
        print(f"❌ Error reading proxies from file: {e}")
        return []


def prepare_httpx_proxy(proxy_string):
    return {
        "http://": f"http://{proxy_string}",
        "https://": f"http://{proxy_string}"
    }


class DarazItem(BaseModel):
    brandId: Optional[str] = None
    brandName: Optional[str] = None
    inStock: Optional[bool] = None
    isSponsored: Optional[bool] = None
    itemId: Optional[str] = None
    itemSoldCntShow: Optional[str] = None
    location: Optional[str] = None
    name: Optional[str] = None
    originalPrice: Optional[str] = None
    price: Optional[str] = None
    ratingScore: Optional[str] = None
    review: Optional[str] = None
    sellerId: Optional[str] = None
    sellerName: Optional[str] = None


async def main():
    tic = time()
    
    browser_headers = await get_scrapeops_headers()
    proxies_list = get_proxyscrape_proxies_local()
    random.shuffle(proxies_list)

    page = 1
    is_last_page = False
    tries = 0
    max_tries = 3

    while not is_last_page:
        tries += 1
        random_headers = random.choice(browser_headers)
        random_proxy = random.choice(proxies_list)
        # proxy_config = prepare_httpx_proxy(random_proxy)
        proxy_url = f"http://{random_proxy}"
    
        target_url = f"https://www.daraz.pk/catalog/?ajax=true&isFirstRequest=true&page={page}&q={quote(PRODUCT)}&spm=a2a0e.tm80335142.search.d_go"

        async with httpx.AsyncClient(proxy=proxy_url) as client:
            response = await client.get(url=target_url, headers=random_headers)
            if response.status_code != 200:
                print(f"❌ Failed page {page} with status: {response.status_code}")
                if tries <= max_tries: continue
                else: break
        
            tries = 0
    
        try:
            json_data = response.json()
            is_last_page = json_data['mainInfo']['noMorePages']
            items = json_data['mods']['listItems']

            with open("daraz_data.jsonl", "a", encoding="utf-8") as file:
                for item in items:
                    file.write(json.dumps(item, ensure_ascii=False) + "\n")

            print(f"✅ Scraped page {page} (200)")
            page += 1
        except Exception as e:
            print(f"⚠️ Failed to parse page {page}: {e}")
            break

    with open("daraz_data.jsonl", "r", encoding="utf-8") as file:
        try:
            dantic_items = [DarazItem(**json.loads(line)) for line in file if line.strip()]
        except Exception as e:
            print(f"❌ Error occurred while converting to pydantic: {e}")
            return

    df = pd.DataFrame(item.model_dump() for item in dantic_items)
    df.to_csv("daraz_data.csv", index=False, encoding="utf-8-sig")

    toc = time()

    print(f"Execution Time: {round(toc-tic, 2)} sec")


if __name__ == "__main__":
    asyncio.run(main())