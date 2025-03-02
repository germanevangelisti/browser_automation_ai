import asyncio
from playwright.async_api import async_playwright
from datetime import datetime


class BrowserController:
    def __init__(self, headless=False):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.page = None
        self.debug_url = None

    async def start(self):
        self.playwright = await async_playwright().start()
        
        # Configuración avanzada para evitar detección como bot
        browser_args = [
            '--disable-blink-features=AutomationControlled',
            '--disable-features=IsolateOrigins,site-per-process',
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            '--remote-debugging-port=9222'  # Puerto para depuración remota
        ]
        
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=browser_args
        )
        
        # Guardamos la URL de depuración para acceder desde el frontend
        self.debug_url = "http://localhost:9222"
        
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            java_script_enabled=True
        )
        
        # Modificar el navigator.webdriver para evitar detección
        await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false,
        });
        """)
        
        self.page = await context.new_page()
        
        # Retornar la URL de depuración
        return self.debug_url

    async def open_url(self, url: str):
        """Open a given URL in the browser."""
        await self.page.goto(url)
        return f"Opened {url}"

    async def close_browser(self):
        """Close the browser instance."""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def screenshot(self, path):
        await self.page.screenshot(path=path)
        # Siempre guardar una copia con nombre "latest" para la UI
        await self.page.screenshot(path="screenshots/browser_screenshot_latest.png")


# Prueba manual
if __name__ == "__main__":
    browser = BrowserController()
    asyncio.run(browser.start())
    print(asyncio.run(browser.open_url("https://www.google.com")))
    asyncio.run(browser.screenshot(f"screenshots/browser_screenshot_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.png"))
    asyncio.run(browser.close_browser())
