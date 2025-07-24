"""
Daraz Product Scraper
----------------------
Asynchronous web scraper for Daraz using rotating headers and proxies.

Features:
- Uses ScrapeOps to simulate real browser headers
- Uses Webshare.io proxies to avoid IP bans
- Concurrent scraping of multiple products
- Cleans and exports data to CSV files
- Validates product data with Pydantic

Environment Variables Required:
- SCRAPEOPS_API_KEY
- WEBSHARE_API_KEY
"""

import os
import json
import random
import asyncio
from time import time
from typing import Optional
from urllib.parse import quote

import httpx
import pandas as pd
from dotenv import load_dotenv
from pydantic import BaseModel

# ----------------------------------------
# Environment Setup
# ----------------------------------------

load_dotenv()

SCRAPEOPS_API_KEY = os.getenv("SCRAPEOPS_API_KEY")
WEBSHARE_API_KEY = os.getenv("WEBSHARE_API_KEY")
SCRAPEOPS_ENDPOINT = "https://headers.scrapeops.io/v1/browser-headers"
PRODUCTS = ["ear pods", "power bank", "smartwatch", "abaya"]
CONCURRENCY = 5

semaphore = asyncio.Semaphore(CONCURRENCY)

# ----------------------------------------
# Models
# ----------------------------------------

class DarazItem(BaseModel):
    brandId: Optional[str]
    brandName: Optional[str]
    inStock: Optional[bool]
    isSponsored: Optional[bool]
    itemId: Optional[str]
    itemSoldCntShow: Optional[str]
    location: Optional[str]
    name: Optional[str]
    originalPrice: Optional[str]
    price: Optional[str]
    ratingScore: Optional[str]
    review: Optional[str]
    sellerId: Optional[str]
    sellerName: Optional[str]

# ----------------------------------------
# Header & Proxy Setup
# ----------------------------------------

async def get_scrapeops_headers():
    async with httpx.AsyncClient(timeout=15) as client:
        params = {'api_key': SCRAPEOPS_API_KEY, 'num_results': 50}
        response = await client.get(SCRAPEOPS_ENDPOINT, params=params)
        return response.json().get("result", [])

async def get_webshare_proxies():
    url = "https://proxy.webshare.io/api/v2/proxy/list/?mode=direct"
    headers = {"Authorization": f"Token {WEBSHARE_API_KEY}"}
    
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(url, headers=headers)
        proxies = response.json().get("results", [])

    return [
        f'http://{p["username"]}:{p["password"]}@{p["proxy_address"]}:{p["port"]}'
        for p in proxies
    ]

# ----------------------------------------
# Scraping Logic
# ----------------------------------------

async def scrape_product(product: str, headers_list, proxies_list):
    async with semaphore:
        page = 1
        retries = 0
        max_retries = 3
        total_items = 0
        done = False

        print(f"\n🔍 Starting scraping for: {product.upper()} 🛒")

        while not done:
            retries += 1
            proxy = random.choice(proxies_list)
            headers = random.choice(headers_list)

            url = (
                "https://www.daraz.pk/catalog/?ajax=true&isFirstRequest=true"
                f"&page={page}&q={quote(product)}&spm=a2a0e.tm80335142.search.d_go"
            )

            async with httpx.AsyncClient(proxy=proxy, timeout=30) as client:
                try:
                    response = await client.get(url, headers=headers)
                except Exception as e:
                    print(f"⚠️ Network error on page {page} [{product}]: {e}")
                    if retries < max_retries:
                        print(f"🔁 Retrying ({retries}/{max_retries})...")
                        continue
                    break

            if response.status_code != 200:
                print(f"❌ Page {page} | {product} ❗Failed (Status {response.status_code})")
                if retries < max_retries:
                    print(f"🔁 Product: {product.capitalize()} Retrying page {page}... Attempt {retries}/{max_retries}")
                    continue
                else:
                    print(f"💥 Max retries exceeded for {product} on page {page}. Skipping.")
                    break

            retries = 0  # reset on success

            try:
                json_data = response.json()
                done = json_data["mainInfo"]["noMorePages"]
                items = json_data["mods"]["listItems"]

                file_path = f"{product.replace(' ', '_')}_data.jsonl"
                with open(file_path, "a", encoding="utf-8") as f:
                    for item in items:
                        f.write(json.dumps(item, ensure_ascii=False) + "\n")

                total_items += len(items)
                print(f"✅ Product: {product.capitalize()} | Page {page} | Scraped {len(items)} items | 📦 Total so far: {total_items}")
                page += 1

            except Exception as e:
                print(f"⚠️ Failed to parse data on page {page} for {product} 🚧 Error: {e}")
                break

        print(f"🔴 Finished scraping {product} ✅ Total pages: {page - 1} | Total items: {total_items}\n")

# ----------------------------------------
# Data Cleaning
# ----------------------------------------

def normalize_sales_count(df: pd.DataFrame) -> pd.DataFrame:
    df[["num", "prefix"]] = df["itemSoldCntShow"].str.extract(r'([\d.]+)([a-zA-Z]?)')
    df["num"] = pd.to_numeric(df["num"], errors="coerce")
    df["prefix"] = df["prefix"].str.lower()

    df["itemSoldCntShow"] = df["num"]
    df.loc[df["prefix"] == "k", "itemSoldCntShow"] = df["num"] * 1_000
    df.loc[df["prefix"] == "m", "itemSoldCntShow"] = df["num"] * 1_000_000

    return df.drop(columns=["num", "prefix"])


def create_csv():
    for product in PRODUCTS:
        file = f"{product.replace(' ', '_')}_data.jsonl"
        try:
            with open(file, "r", encoding="utf-8") as f:
                items = [DarazItem(**json.loads(line)) for line in f if line.strip()]
        except Exception as e:
            print(f"❌ {product} - JSONL read error: {e}")
            continue

        df = pd.DataFrame(item.model_dump() for item in items)
        df = normalize_sales_count(df)
        df.to_csv(f"{product.replace(' ', '_')}_data.csv", index=False, encoding="utf-8-sig")

        print(f"📄 CSV created for {product}")

# ----------------------------------------
# Entry Point
# ----------------------------------------

async def main():
    browser_headers = await get_scrapeops_headers()
    proxies = await get_webshare_proxies()

    random.shuffle(browser_headers)
    random.shuffle(proxies)

    tasks = [scrape_product(product, browser_headers, proxies) for product in PRODUCTS]
    await asyncio.gather(*tasks)

    create_csv()


if __name__ == "__main__":
    start = time()
    asyncio.run(main())
    end = time()
    print(f"\n⏰ Finished in {round(end - start, 2)} seconds")
