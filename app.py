import time
import random
import asyncio
import aiohttp
from playwright.async_api import async_playwright
from fake_useragent import UserAgent
import requests
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from urllib.parse import urlparse, quote_plus
import re
import subprocess
import platform
import os
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'seo_traffic_booster_secret')
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*")

class SEOTrafficBooster:
    def __init__(self):
        self.ua = UserAgent()
        self.is_running = False
        self.current_status = "Ready"
        self.current_cycle = 0
        self.total_cycles = 0
        self.current_proxy = None
        self.current_target_website = None
        
    def update_status(self, message):
        """Update status dan kirim ke UI"""
        self.current_status = message
        timestamp = time.strftime("%H:%M:%S")
        socketio.emit('status_update', {
            'message': f"[{timestamp}] {message}",
            'cycle': self.current_cycle,
            'total_cycles': self.total_cycles,
            'current_proxy': self.current_proxy
        })
        print(f"[{timestamp}] {message}")
    
    async def setup_browser(self, proxy_list):
        """Setup Playwright browser dengan Async API"""
        try:
            playwright = await async_playwright().start()
            
            # Proxy configuration
            proxy_arg = None
            if proxy_list:
                proxy = random.choice(proxy_list)
                self.current_proxy = proxy
                self.update_status(f"Using proxy: {proxy}")
                proxy_arg = {
                    'server': proxy
                }
            else:
                self.current_proxy = None
                self.update_status("Running without proxy")

            # Browser launch options
            launch_options = {
                'headless': True,
                'args': [
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--ignore-certificate-errors',
                    '--ignore-ssl-errors',
                    '--disable-gpu',
                    '--window-size=1280,720'
                ]
            }

            if proxy_arg:
                launch_options['proxy'] = proxy_arg

            browser = await playwright.chromium.launch(**launch_options)

            # Context options
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent=self.ua.random,
                ignore_https_errors=True
            )

            # Stealth script
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            """)

            page = await context.new_page()
            await page.set_default_timeout(30000)
            
            return playwright, browser, context, page

        except Exception as e:
            self.update_status(f"Browser setup error: {str(e)}")
            return None, None, None, None
    
    def generate_keywords_from_url(self, url):
        """Generate keyword SEO otomatis dari URL"""
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.replace('www.', '')
            
            if 'blogspot.com' in domain:
                blog_name = domain.replace('.blogspot.com', '')
                keywords = [blog_name, f"{blog_name} blog", f"{blog_name} articles"]
            else:
                domain_keywords = domain.replace('.com', '').split('.')
                keywords = [kw for kw in domain_keywords if kw and len(kw) > 2]
            
            return keywords[:10] if keywords else ["blog", "articles", "website"]
        
        except Exception as e:
            self.update_status(f"Keyword generation error: {str(e)}")
            return ["blog", "articles", "posts"]
    
    def build_google_search_url(self, keyword):
        """Bangun URL pencarian Google"""
        encoded_keyword = quote_plus(keyword)
        return f"https://www.google.com/search?q={encoded_keyword}"
    
    async def simulate_human_behavior(self, page, keyword, target_website):
        """Simulasi perilaku manusia dengan Async API"""
        try:
            self.current_target_website = target_website
            
            # Google search
            search_url = self.build_google_search_url(keyword)
            self.update_status(f"🔍 Searching: {keyword}")
            
            await page.goto(search_url, wait_until='domcontentloaded')
            await asyncio.sleep(random.uniform(3, 5))
            
            # Cari link target
            all_links = await page.query_selector_all("a")
            target_links = []
            
            for link in all_links:
                try:
                    href = await link.get_attribute('href')
                    if href and target_website in href:
                        target_links.append(link)
                except:
                    continue
            
            if target_links:
                link = random.choice(target_links)
                self.update_status("✅ Found target link, clicking...")
                await link.click()
                await asyncio.sleep(random.uniform(5, 8))
                
                # Aktivitas di website target
                self.update_status("🖱️ Clicking Google Ads...")
                await self.click_google_ads(page)
                
                self.update_status("📖 Reading random post...")
                await self.read_random_post(page)
                
                return True
            else:
                self.update_status("🌐 Direct website access...")
                return await self.direct_website_access(page, target_website)
                
        except Exception as e:
            self.update_status(f"❌ Simulation error: {str(e)}")
            return await self.direct_website_access(page, target_website)
    
    async def click_google_ads(self, page):
        """Klik iklan Google Ads"""
        try:
            ads_selectors = [
                "a[href*='googleadservices.com']",
                ".adsbygoogle",
                "[data-ad-client]"
            ]
            
            for selector in ads_selectors:
                try:
                    ads = await page.query_selector_all(selector)
                    if ads:
                        ad = random.choice(ads)
                        await ad.scroll_into_view_if_needed()
                        await asyncio.sleep(1)
                        await ad.click()
                        self.update_status("🖱️ Clicked ad, waiting...")
                        await asyncio.sleep(random.uniform(8, 12))
                        await page.go_back(wait_until='domcontentloaded')
                        await asyncio.sleep(2)
                        return True
                except:
                    continue
            return False
        except Exception as e:
            self.update_status(f"Ad click error: {str(e)}")
            return False
    
    async def read_random_post(self, page):
        """Baca postingan acak"""
        try:
            post_selectors = [
                "a[href*='/p/']",
                "a[href*='/post/']", 
                "a[href*='/article/']",
                "a.entry-title",
                "a.post-title"
            ]
            
            for selector in post_selectors:
                try:
                    posts = await page.query_selector_all(selector)
                    if posts:
                        post = random.choice(posts)
                        post_text = await post.text_content()
                        post_text = post_text[:30] + "..." if post_text else "post"
                        self.update_status(f"📚 Reading: {post_text}...")
                        await post.click()
                        await asyncio.sleep(3)
                        
                        # Scroll seperti membaca
                        await self.reading_scroll_behavior(page)
                        await asyncio.sleep(random.uniform(15, 25))
                        
                        await page.go_back(wait_until='domcontentloaded')
                        return True
                except:
                    continue
            return False
        except Exception as e:
            self.update_status(f"Reading error: {str(e)}")
            return False
    
    async def reading_scroll_behavior(self, page):
        """Scroll behavior untuk membaca"""
        try:
            total_height = await page.evaluate("() => document.body.scrollHeight")
            current_pos = 0
            
            while current_pos < total_height - 800:
                scroll_amount = random.randint(200, 400)
                current_pos += scroll_amount
                await page.evaluate(f"window.scrollTo(0, {current_pos})")
                await asyncio.sleep(random.uniform(1, 3))
        except:
            pass
    
    async def direct_website_access(self, page, target_website):
        """Akses website langsung"""
        try:
            await page.goto(target_website, wait_until='domcontentloaded')
            await asyncio.sleep(random.uniform(5, 8))
            
            # Aktivitas di website
            await self.click_google_ads(page)
            await self.read_random_post(page)
            
            return True
        except Exception as e:
            self.update_status(f"Direct access error: {str(e)}")
            return False
    
    async def run_async_cycles(self, keywords, target_website, cycles, delay_between_cycles, proxy_list):
        """Jalankan cycles dengan Async API"""
        self.is_running = True
        self.total_cycles = cycles
        self.current_cycle = 0
        
        if not keywords:
            keywords = self.generate_keywords_from_url(target_website)
        
        for cycle in range(cycles):
            if not self.is_running:
                break
                
            self.current_cycle = cycle + 1
            self.update_status(f"🔄 Cycle {self.current_cycle}/{cycles}")
            
            playwright, browser, context, page = await self.setup_browser(proxy_list)
            if not browser:
                continue
            
            try:
                keyword = random.choice(keywords)
                success = await self.simulate_human_behavior(page, keyword, target_website)
                
                if success:
                    self.update_status(f"✅ Cycle {self.current_cycle} completed")
                else:
                    self.update_status(f"⚠️ Cycle {self.current_cycle} had issues")
                
            except Exception as e:
                self.update_status(f"❌ Cycle error: {str(e)}")
            finally:
                try:
                    await context.close()
                    await browser.close()
                    await playwright.stop()
                except:
                    pass
            
            if cycle < cycles - 1 and self.is_running:
                self.update_status(f"⏳ Waiting {delay_between_cycles} seconds...")
                for i in range(delay_between_cycles):
                    if not self.is_running:
                        break
                    await asyncio.sleep(1)
        
        self.is_running = False
        self.update_status("🎉 All cycles completed!")
    
    def run_cycles(self, keywords, target_website, cycles, delay_between_cycles, proxy_list):
        """Wrapper untuk menjalankan async cycles dari thread"""
        # Buat event loop baru untuk thread ini
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(
                self.run_async_cycles(keywords, target_website, cycles, delay_between_cycles, proxy_list)
            )
        finally:
            loop.close()

# Global instance
booster = SEOTrafficBooster()

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    emit('status_update', {
        'message': f"[{time.strftime('%H:%M:%S')}] Connected to SEO Traffic Booster",
        'cycle': booster.current_cycle,
        'total_cycles': booster.total_cycles,
        'current_proxy': booster.current_proxy
    })

@socketio.on('start_cycles')
def handle_start_cycles(data):
    if booster.is_running:
        emit('error', {'message': 'Booster is already running!'})
        return
    
    keywords = [k.strip() for k in data['keywords'].split('\n') if k.strip()]
    target_website = data['website'].strip()
    cycles = int(data['cycles'])
    delay = int(data['delay'])
    proxy_list = [p.strip() for p in data['proxies'].split('\n') if p.strip()] 
    
    if not target_website:
        emit('error', {'message': 'Please enter target website!'})
        return
    
    thread = threading.Thread(
        target=booster.run_cycles,
        args=(keywords, target_website, cycles, delay, proxy_list)
    )
    thread.daemon = True
    thread.start()
    
    emit('start_success', {'message': 'SEO Booster started!'})

@socketio.on('stop_cycles')
def handle_stop_cycles():
    booster.is_running = False
    emit('stop_success', {'message': 'Stopping booster...'})

if __name__ == '__main__':
    socketio.run(app, debug=False, host='0.0.0.0', port=5000)
