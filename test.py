import asyncio
import httpx
import random
import json
from urllib.parse import quote, urlencode
from time import time
from pydantic import BaseModel
from typing import Optional
import pandas as pd

SCRAPINGANT_API_KEY = "your_scrapingant_key"
SCRAPINGANT_BASE_URL = "https://api.scrapingant.com/v2/general"
SCRAPEOPS_API_KEY = 'your_scrapeops_key'
SCRAPEOPS_ENDPOINT = 'https://headers.scrapeops.io/v1/browser-headers'

PRODUCTS = ["smartwatch", "ear pods", "laptop bag"]

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

def build_scrapingant_url(product, page):
    target_url = f"https://www.daraz.pk/catalog/?ajax=true&isFirstRequest=true&page={page}&q={quote(product)}&spm=a2a0e.tm80335142.search.d_go"
    params = {
        'url': target_url,
        'x-api-key': SCRAPINGANT_API_KEY,
        'browser': 'false'
    }
    return f"{SCRAPINGANT_BASE_URL}?{urlencode(params)}"

async def get_scrapeops_headers():
    async with httpx.AsyncClient() as client:
        params = {'api_key': SCRAPEOPS_API_KEY, 'num_results': 50}
        r = await client.get(SCRAPEOPS_ENDPOINT, params=params)
        return r.json().get("result", [])

async def scrape_product(product, headers_list):
    async with httpx.AsyncClient(timeout=60) as client:
        is_last_page = False
        page = 1
        while not is_last_page:
            url = build_scrapingant_url(product, page)
            random_headers = random.choice(headers_list)
            try:
                response = await client.get(url, headers=random_headers)
                if response.status_code != 200:
                    print(f"❌ {product} page {page}: {response.status_code}")
                    break
                json_data = response.json()
                is_last_page = json_data['mainInfo']['noMorePages']
                items = json_data['mods']['listItems']

                with open(f"{product.replace(' ', '_')}.jsonl", "a", encoding="utf-8") as f:
                    for item in items:
                        f.write(json.dumps(item, ensure_ascii=False) + "\n")

                print(f"✅ {product} page {page}")
                page += 1
                await asyncio.sleep(random.uniform(2, 4))  # Delay between pages
            except Exception as e:
                print(f"⚠️ Error scraping {product} page {page}: {e}")
                break

async def main():
    tic = time()
    headers_list = await get_scrapeops_headers()

    # Run a limited number of products concurrently, then wait to avoid 409
    batch_size = 2
    for i in range(0, len(PRODUCTS), batch_size):
        current_batch = PRODUCTS[i:i+batch_size]
        await asyncio.gather(*(scrape_product(p, headers_list) for p in current_batch))
        await asyncio.sleep(5)  # Wait before starting next batch

    toc = time()
    print(f"✅ Done in {round(toc - tic, 2)} sec")

if __name__ == "__main__":
    asyncio.run(main())
