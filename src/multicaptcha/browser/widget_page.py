from urllib.parse import urlsplit

from playwright.async_api import Page, Route


async def open_widget_page(page: Page, url: str, html: str) -> None:
    """Show `html` at `url` without contacting that page, so the widget sees its origin.

    Only the top-level document is replaced; widget iframes and scripts load
    normally, even when they share the host (as in Google's own demo).
    """

    async def serve(route: Route) -> None:
        request = route.request
        if request.is_navigation_request() and request.frame.parent_frame is None:
            await route.fulfill(status=200, content_type="text/html", body=html)
        else:
            await route.continue_()

    host = urlsplit(url).netloc.lower()
    await page.route(lambda u: urlsplit(u).netloc.lower() == host, serve)
    await page.goto(url, wait_until="domcontentloaded")
