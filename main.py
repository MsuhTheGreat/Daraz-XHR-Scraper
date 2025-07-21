import httpx
import asyncio
import random
import json
from urllib.parse import quote
from time import time
from pydantic import BaseModel
from typing import Optional
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Constants
SCRAPEOPS_ENDPOINT = 'https://headers.scrapeops.io/v1/browser-headers'
SCRAPEOPS_API_KEY = os.getenv("SCRAPEOPS_API_KEY")
WEBSHARE_API_KEY = os.getenv("WEBSHARE_API_KEY")
PRODUCTS = ["ear pods", "power bank", "smartwatch", "abaya"]
CONCURRENCY = 5

# Limit concurrent scraping tasks
semaphore = asyncio.Semaphore(CONCURRENCY)


async def get_scrapeops_headers():
    """
    Fetch fake browser headers from ScrapeOps to simulate real browser traffic.
    """
    async with httpx.AsyncClient(timeout=15) as client:
        params = {'api_key': SCRAPEOPS_API_KEY, 'num_results': 50}
        response = await client.get(SCRAPEOPS_ENDPOINT, params=params)
        return response.json().get("result", [])


async def get_webshare_proxies():
    """
    Fetch proxy list from Webshare.io using API key authentication.
    Returns a list of proxy URLs with embedded credentials.
    """
    headers = {
        "Authorization": f"Token {WEBSHARE_API_KEY}"
    }
    url = "https://proxy.webshare.io/api/v2/proxy/list/?mode=direct"
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(url, headers=headers)
        data = response.json()

    # Construct proxy URLs from API response
    proxy_list = [
        f'http://{result["username"]}:{result["password"]}@{result["proxy_address"]}:{result["port"]}'
        for result in data['results']
    ]
    return proxy_list


class DarazItem(BaseModel):
    """
    Pydantic model to validate and structure product data.
    """
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


async def scrape_product(product:str, browser_headers, proxies_list):
    """
    Scrape product listings for a given product keyword across multiple pages.
    Now with improved logging for better UX.
    """
    async with semaphore:
        page = 1
        is_last_page = False
        tries = 0
        max_tries = 3
        total_scraped = 0

        print(f"\n🔍 Starting scrape for: {product.upper()} 🛒")

        while not is_last_page:
            tries += 1
            random_headers = random.choice(browser_headers)
            random_proxy = random.choice(proxies_list)

            # Encode product name into URL
            target_url = (
                f"https://www.daraz.pk/catalog/?ajax=true&isFirstRequest=true"
                f"&page={page}&q={quote(product)}&spm=a2a0e.tm80335142.search.d_go"
            )

            async with httpx.AsyncClient(proxy=random_proxy, timeout=30) as client:
                response = await client.get(url=target_url, headers=random_headers)

                if response.status_code != 200:
                    print(f"❌ Page {page} | {product} ❗️Failed (Status {response.status_code})")
                    if tries <= max_tries:
                        print(f"🔁 Product: {product.capitalize()} Retrying page {page}... Attempt {tries}/{max_tries}")
                        continue
                    else:
                        print(f"💥 Max retries exceeded for {product} on page {page}. Skipping.")
                        break

                tries = 0  # Reset tries on success

            try:
                await response.aread()
                json_data = response.json()
                is_last_page = json_data['mainInfo']['noMorePages']
                items = json_data['mods']['listItems']

                with open(f"{product.replace(' ', '_')}_data.jsonl", "a", encoding="utf-8") as file:
                    for item in items:
                        file.write(json.dumps(item, ensure_ascii=False) + "\n")

                total_scraped += len(items)
                print(f"✅ Product: {product.capitalize()} | Page {page} | Scraped {len(items)} items | 📦 Total so far: {total_scraped}")
                page += 1

            except Exception as e:
                print(f"⚠️ Failed to parse data on page {page} for {product} 🚧 Error: {e}")
                break

        print(f"🏁 Finished scraping {product} ✅ Total pages: {page - 1} | Total items: {total_scraped}\n")


def create_csv():
    """
    Convert all JSONL product files into cleaned CSVs using Pydantic validation.
    It also normalizes the itemSoldCntShow field for better numeric analysis.
    """
    for product in PRODUCTS:
        with open(f"{product.replace(' ', '_')}_data.jsonl", "r", encoding="utf-8") as file:
            try:
                dantic_items = [DarazItem(**json.loads(line)) for line in file if line.strip()]
            except Exception as e:
                print(f"❌ Product: {product} Error occurred while converting to Pydantic: {e}")
                return

        # Convert Pydantic models to DataFrame
        df = pd.DataFrame(item.model_dump() for item in dantic_items)

        # Clean up itemSoldCntShow (e.g., "1.2k", "3M")
        df[["num", "prefix"]] = df["itemSoldCntShow"].str.extract(r'([\d.]+)([a-zA-Z]?)')
        df["num"] = pd.to_numeric(df["num"], errors="coerce")
        df["prefix"] = df["prefix"].str.lower()

        # Convert abbreviated counts to actual numbers
        df["itemSoldCntShow"] = df["num"].where(df["prefix"] == "", df["num"])
        df.loc[df["prefix"] == "k", "itemSoldCntShow"] = df["num"] * 1000
        df.loc[df["prefix"] == "m", "itemSoldCntShow"] = df["num"] * 1_000_000

        df.drop(columns=["num", "prefix"], inplace=True)

        # Export to CSV
        df.to_csv(f"{product.replace(' ', '_')}_data.csv", index=False, encoding="utf-8-sig")
        print(f"📄 CSV created for {product}")


async def main():
    """
    Main async entrypoint: fetch headers, proxies, and scrape all products.
    """
    browser_headers = await get_scrapeops_headers()
    proxies_list = await get_webshare_proxies()

    # Shuffle to randomize usage
    random.shuffle(browser_headers)
    random.shuffle(proxies_list)

    # Create tasks for each product
    tasks = [scrape_product(product, browser_headers, proxies_list) for product in PRODUCTS]
    await asyncio.gather(*tasks)

    # Convert raw data to CSV
    create_csv()


if __name__ == "__main__":
    tic = time()
    asyncio.run(main())
    toc = time()
    print(f"\n🚀 Execution Time: {round(toc - tic, 2)} sec")
