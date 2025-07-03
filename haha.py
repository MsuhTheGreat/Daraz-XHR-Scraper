import httpx
import asyncio
import random
import json
from urllib.parse import quote
from time import time
from pydantic import BaseModel
from typing import Optional
import pandas as pd
from env import SCRAPEOPS_API_KEY, WEBSHARE_API_KEY

SCRAPINGANT_BASE_URL = "https://api.scrapingant.com/v2/general"
SCRAPEOPS_ENDPOINT = 'https://headers.scrapeops.io/v1/browser-headers'
PRODUCTS = ["ear pods", "power bank", "smartwatch", "abaya"]
CONCURRENCY = 5

semaphore = asyncio.Semaphore(CONCURRENCY)

async def get_scrapeops_headers():
    async with httpx.AsyncClient(timeout=15) as client:
        params = {'api_key': SCRAPEOPS_API_KEY, 'num_results': 50}
        response = await client.get(SCRAPEOPS_ENDPOINT, params=params)
        return response.json().get("result", [])


async def get_webshare_proxies():
    headers = {
        "Authorization": f"Token {WEBSHARE_API_KEY}"
    }
    url = "https://proxy.webshare.io/api/v2/proxy/list/?mode=direct"
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(url, headers=headers)
        data = response.json()
    proxy_list = [f'http://{result["username"]}:{result["password"]}@{result["proxy_address"]}:{result["port"]}' for result in data['results']]
    return proxy_list


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


async def scrape_product(product, browser_headers, proxies_list):
    async with semaphore:
        page = 1
        is_last_page = False
        tries = 0
        max_tries = 3

        while not is_last_page:
            tries += 1
            random_headers = random.choice(browser_headers)
            random_proxy = random.choice(proxies_list)
            
            target_url = f"https://www.daraz.pk/catalog/?ajax=true&isFirstRequest=true&page={page}&q={quote(product)}&spm=a2a0e.tm80335142.search.d_go"

            async with httpx.AsyncClient(proxy=random_proxy, timeout=30) as client:
                response = await client.get(url=target_url, headers=random_headers)
                if response.status_code != 200:
                    print(f"❌ Product: {product} Failed page {page} with status: {response.status_code}")
                    if tries <= max_tries: continue
                    else: break
            
                tries = 0
        
            try:
                await response.aread()
                json_data = response.json()
                is_last_page = json_data['mainInfo']['noMorePages']
                items = json_data['mods']['listItems']

                with open(f"{product.replace(' ', '_')}_data.jsonl", "a", encoding="utf-8") as file:
                    for item in items:
                        file.write(json.dumps(item, ensure_ascii=False) + "\n")

                print(f"✅ Product: {product} Scraped page {page} (200)")
                page += 1
            except Exception as e:
                print(f"⚠️ Product: {product} Failed to parse page {page}: {e}")


def create_csv():
    for product in PRODUCTS:
        with open(f"{product.replace(' ', '_')}_data.jsonl", "r", encoding="utf-8") as file:
            try:
                dantic_items = [DarazItem(**json.loads(line)) for line in file if line.strip()]
            except Exception as e:
                print(f"❌ Product: {product} Error occurred while converting to pydantic: {e}")
                return

        df = pd.DataFrame(item.model_dump() for item in dantic_items)
        df.to_csv(f"{product.replace(' ', '_')}_data.csv", index=False, encoding="utf-8-sig")


async def main():
    browser_headers = await get_scrapeops_headers()
    proxies_list = await get_webshare_proxies()
    random.shuffle(browser_headers)
    random.shuffle(proxies_list)
    
    tasks = [scrape_product(product, browser_headers, proxies_list) for product in PRODUCTS]
    await asyncio.gather(*tasks)
    create_csv()
    

if __name__ == "__main__":
    tic = time()
    asyncio.run(main())
    toc = time()
    print(f"Execution Time: {round(toc-tic, 2)} sec")