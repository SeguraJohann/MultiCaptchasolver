"""End-to-end demo: read the sitekey, get a token from the API, submit the form."""

import argparse
import asyncio
import os

import httpx
from playwright.async_api import async_playwright

URL = "https://www.google.com/recaptcha/api2/demo"


async def run(server: str, headless: bool) -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="chromium", headless=headless)
        page = await browser.new_page(locale="en-US")
        await page.goto(URL)
        sitekey = await page.locator("[data-sitekey]").first.get_attribute("data-sitekey")
        print(f"sitekey: {sitekey}")

        async with httpx.AsyncClient(timeout=180) as client:
            response = await client.post(
                f"{server}/solve",
                json={
                    "type": "recaptcha_v2",
                    "url": URL,
                    "sitekey": sitekey,
                    "transcriber": "whisper",
                },
                headers={"X-API-Key": os.environ.get("API_KEY", "")},
            )
        if response.status_code != 200:
            raise SystemExit(f"solver error {response.status_code}: {response.text}")
        data = response.json()
        print(f"token ({data['elapsed_seconds']}s): {data['token'][:40]}...")

        field = page.locator('textarea[name="g-recaptcha-response"]')
        await field.evaluate("(el, token) => { el.value = token; }", data["token"])
        async with page.expect_navigation():
            await page.locator("form").first.evaluate(
                "f => HTMLFormElement.prototype.submit.call(f)"
            )
        print("page says:", (await page.locator("body").inner_text()).strip()[:200])
        if not headless:
            await asyncio.to_thread(input, "Press Enter to close...")
        await browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="demo")
    parser.add_argument("--server", default="http://127.0.0.1:8000")
    parser.add_argument("--headless", action="store_true")
    args = parser.parse_args()
    asyncio.run(run(args.server, args.headless))
