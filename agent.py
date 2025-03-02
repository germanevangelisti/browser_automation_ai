from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from browser_controller import BrowserController
import os
import json
from datetime import datetime
import asyncio
import random


class BrowserAgent:
    def __init__(self, model="gpt-4", headless=True):
        self.llm = ChatOpenAI(model_name=model, api_key=os.getenv("OPENAI_API_KEY"))
        self.browser = BrowserController(headless=headless)

    async def start_browser(self):
        debug_url = await self.browser.start()
        print(f"Browser started with debug URL: {debug_url}")

    async def translate_to_json(self, command: str):
        """Use LangChain to translate user command into structured JSON"""
        prompt = f"""
        You are an AI that translates natural language instructions into JSON for browser automation. You need to identify the correct selectors for different websites automatically.

        Some common selectors by website:
        - Google: #APjFqb, or input[type="text"]
        - YouTube: input[name="search_query"], #search, or .ytSearchboxComponentInput
          - YouTube video results: ytd-video-renderer, #video-title
        - Twitter/X: input[data-testid="SearchBox_Search_Input"], input[placeholder="Search"]
        - Amazon: input[name="field-keywords"], #twotabsearchtextbox
          - Amazon product results: div[data-component-type="s-search-result"]
        - Generic search boxes: input[type="search"], input[type="text"], [role="search"] input, [placeholder*="search" i]

        Selectors for results/items:
        - YouTube videos: ytd-video-renderer, #video-title
        - Google search results: .g .yuRUbf a, h3.LC20lb
        - Shopping results: .product-item, .product-card, [data-testid*="result"]
        
        For ordinal positions (first, second, third...), you can use :nth-child(), :nth-of-type() or array indexes.

        Choose the most specific and reliable selector for the website being automated. If the site is not specified, think about which site would be appropriate for the task.

        Examples:

        User: 'Open Google and search for LangChain'
        AI: {{
            "browser": "chromium",
            "headless": false,
            "actions": [
                {{"type": "open_url", "value": "https://www.google.com"}},
                {{"type": "input", "selector": "#APjFqb", "value": "LangChain"}},
                {{"type": "press", "selector": "#APjFqb", "key": "Enter"}}
            ]
        }}

        User: 'Go to YouTube, search for piano music and play the first video'
        AI: {{
            "browser": "chromium",
            "headless": false,
            "actions": [
                {{"type": "open_url", "value": "https://www.youtube.com"}},
                {{"type": "input", "selector": "input[name='search_query']", "value": "piano music"}},
                {{"type": "press", "selector": "input[name='search_query']", "key": "Enter"}},
                {{"type": "wait", "time": 2000}},
                {{"type": "click", "selector": "ytd-video-renderer:nth-child(1) #video-title"}}
            ]
        }}

        User: 'Search for shoes on Amazon and open the second result'
        AI: {{
            "browser": "chromium", 
            "headless": false,
            "actions": [
                {{"type": "open_url", "value": "https://www.amazon.com"}},
                {{"type": "input", "selector": "#twotabsearchtextbox", "value": "shoes"}},
                {{"type": "press", "selector": "#twotabsearchtextbox", "key": "Enter"}},
                {{"type": "wait", "time": 2000}},
                {{"type": "click", "selector": "div[data-component-type='s-search-result']:nth-child(2) h2 a"}}
            ]
        }}

        User: '{command}'
        AI:
        """

        response = self.llm.invoke(
            [
                SystemMessage(content="You are a JSON automation assistant specialized in identifying proper web selectors."),
                HumanMessage(content=prompt),
            ]
        )
        print("Response: \n", response.content)
        try:
            actions = json.loads(response.content)
            return actions
        except json.JSONDecodeError:
            return {"error": "Invalid JSON response from AI"}

    async def execute_from_text(self, command: str):
        """Translate command to JSON and execute"""
        actions = await self.translate_to_json(command)
        if "error" in actions:
            return actions["error"]
        return await self.execute_actions(actions["actions"])

    async def execute_actions(self, actions):
        """Executes structured actions in Playwright with fallback selectors"""
        for action in actions:
            if action["type"] == "open_url":
                await self.browser.open_url(action["value"])
                # Dar tiempo a que la página cargue completamente
                await asyncio.sleep(2)
                
            elif action["type"] == "input":
                # Intentar con el selector proporcionado
                try:
                    await self.browser.page.wait_for_selector(action["selector"], timeout=5000)
                    await self.move_mouse_humanlike(200, 200)
                    await self.browser.page.fill(action["selector"], action["value"])
                except Exception as e:
                    print(f"Error with primary selector: {str(e)}")
                    # Intentar con selectores alternativos comunes
                    fallback_selectors = [
                        "input[type='search']",
                        "input[type='text']",
                        "input[name='search']",
                        "input[name='search_query']",
                        "#APjFqb",
                        ".search-box",
                        "#search"
                    ]
                    
                    for selector in fallback_selectors:
                        try:
                            if await self.browser.page.query_selector(selector):
                                print(f"Using fallback selector: {selector}")
                                await self.browser.page.fill(selector, action["value"])
                                action["selector"] = selector  # Actualizar el selector para la acción de presionar
                                break
                        except Exception as e:
                            continue
                            
            elif action["type"] == "press":
                try:
                    await self.browser.page.wait_for_selector(action["selector"], timeout=5000)
                    await self.browser.page.press(action["selector"], action["key"])
                except Exception as e:
                    print(f"Error pressing key: {str(e)}")
                    # Si falló la acción de presionar, intentar con Enter en el último selector que funcionó
                    try:
                        await self.browser.page.keyboard.press("Enter")
                    except Exception as e:
                        pass
            
            elif action["type"] == "click":
                try:
                    # Esperar a que el selector esté disponible
                    await self.browser.page.wait_for_selector(action["selector"], timeout=5000)
                    
                    # Obtener el elemento
                    element = await self.browser.page.query_selector(action["selector"])
                    
                    if element:
                        # Obtener la posición del elemento para un clic más natural
                        bounding_box = await element.bounding_box()
                        if bounding_box:
                            # Mover el ratón de manera natural hacia el elemento
                            x = bounding_box["x"] + bounding_box["width"] / 2
                            y = bounding_box["y"] + bounding_box["height"] / 2
                            await self.move_mouse_humanlike(x, y, radius=10, loops=1)
                            
                            # Realizar el clic
                            await self.browser.page.click(action["selector"])
                            print(f"Clicked on element: {action['selector']}")
                        else:
                            # Si no podemos obtener la caja delimitadora, intentamos un clic directo
                            await self.browser.page.click(action["selector"])
                    else:
                        # Si el selector no encuentra ningún elemento, intentar con selectores alternativos
                        print(f"Element not found with selector: {action['selector']}")
                        await self.try_alternative_selectors_for_click(action)
                except Exception as e:
                    print(f"Error clicking element: {str(e)}")
                    await self.try_alternative_selectors_for_click(action)
                    
            elif action["type"] == "wait":
                await asyncio.sleep(action.get("time", 1000) / 1000)
                
            elif action["type"] == "screenshot":
                await self.browser.page.screenshot(path=action["path"])
                
            # Pequeña pausa entre acciones para simular comportamiento humano
            await self.delay_action(random.randint(500, 1500))
                
        return "Actions executed"
    
    async def try_alternative_selectors_for_click(self, action):
        """Intenta utilizar selectores alternativos cuando el clic falla"""
        website_url = await self.browser.page.url()
        
        # Definir selectores alternativos según el sitio web
        alternative_selectors = []
        
        if "youtube.com" in website_url:
            alternative_selectors = [
                "ytd-video-renderer a#video-title",
                "ytd-video-renderer a.yt-simple-endpoint",
                "#contents ytd-video-renderer:first-child",
                "ytd-video-renderer:nth-child(1)",
                "ytd-video-renderer"
            ]
        elif "google.com" in website_url:
            alternative_selectors = [
                ".g .yuRUbf a", 
                "h3.LC20lb", 
                ".g a", 
                "div.g:first-child a",
                ".rc .r a"
            ]
        elif "amazon.com" in website_url:
            alternative_selectors = [
                "div[data-component-type='s-search-result'] h2 a",
                ".s-result-item h2 a",
                ".s-search-results .s-result-item:first-child h2 a",
                ".s-result-list .s-result-item a.a-link-normal"
            ]
        else:
            # Selectores genéricos que podrían funcionar en diferentes sitios
            alternative_selectors = [
                "a.result", 
                ".search-result a", 
                ".results a:first-child",
                ".results li:first-child a",
                "article a",
                ".card a",
                "a[href]"
            ]
            
        # Intentar cada selector alternativo
        for selector in alternative_selectors:
            try:
                if await self.browser.page.query_selector(selector):
                    print(f"Using alternative selector for click: {selector}")
                    await self.browser.page.click(selector)
                    return True
            except Exception as e:
                continue
                
        print("Failed to click with all alternative selectors")
        return False

    async def move_mouse_humanlike(self, x, y, radius=20, loops=1):
        """Mueve el ratón en un patrón circular para simular comportamiento humano"""
        import asyncio
        import math
        
        # Primero movemos el ratón a la posición inicial
        await self.browser.page.mouse.move(x, y)
        
        # Luego realizamos movimientos circulares
        steps = 20  # Número de pasos para completar un círculo
        for loop in range(loops):
            for step in range(steps):
                angle = 2 * math.pi * step / steps
                new_x = x + radius * math.cos(angle)
                new_y = y + radius * math.sin(angle)
                
                # Añadimos una pequeña variación aleatoria para hacerlo más natural
                import random
                jitter = random.uniform(-2, 2)
                new_x += jitter
                new_y += jitter
                
                await self.browser.page.mouse.move(new_x, new_y)
                await asyncio.sleep(0.01)  # Pequeña pausa entre movimientos
                
    async def delay_action(self, milliseconds=500):
        """Simula un retraso entre acciones"""
        import asyncio
        await asyncio.sleep(milliseconds / 1000)

    async def close(self):
        await self.browser.close_browser()

    async def screenshot(self):
        await self.browser.screenshot(
            path=f"screenshots/browser_screenshot_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.png"
        )
