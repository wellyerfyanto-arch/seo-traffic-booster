import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from fake_useragent import UserAgent
import requests
import os

class SEOTrafficBooster:
    def __init__(self):
        self.ua = UserAgent()
        self.proxies = self.load_proxies()
        
    def load_proxies(self):
        # Load proxies from file or API
        try:
            with open('proxies.txt', 'r') as f:
                proxies = [line.strip() for line in f.readlines()]
            return proxies
        except:
            return self.get_free_proxies()
    
    def get_free_proxies(self):
        # Get free US proxies from various sources
        sources = [
            'https://www.proxy-list.download/api/v1/get?type=http&country=US',
            'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=US'
        ]
        
        proxies = []
        for source in sources:
            try:
                response = requests.get(source, timeout=10)
                proxies.extend(response.text.split('\r\n'))
            except:
                continue
        
        return [p for p in proxies if p]
    
    def setup_driver(self):
        chrome_options = Options()
        
        # Random User Agent
        chrome_options.add_argument(f'--user-agent={self.ua.random}')
        
        # Proxy settings
        if self.proxies:
            proxy = random.choice(self.proxies)
            chrome_options.add_argument(f'--proxy-server=http://{proxy}')
        
        # Headless mode
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return driver
        except Exception as e:
            print(f"Error setting up driver: {e}")
            return None
    
    def check_ip_leak(self, driver):
        try:
            driver.get("https://api.ipify.org")
            current_ip = driver.find_element(By.TAG_NAME, 'body').text
            print(f"Current IP: {current_ip}")
            return True
        except:
            return False
    
    def google_login(self, driver):
        try:
            driver.get("https://accounts.google.com")
            time.sleep(3)
            
            # Random email (replace with your accounts)
            emails = ["test1@gmail.com", "test2@gmail.com"]
            email = random.choice(emails)
            
            # Login process (simplified - you'll need to implement actual login)
            print(f"Attempting login with: {email}")
            time.sleep(2)
            
        except Exception as e:
            print(f"Login error: {e}")
    
    def simulate_visit(self, driver, keyword, target_website):
        try:
            # Google Search
            driver.get("https://www.google.com")
            search_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            
            search_box.send_keys(keyword)
            search_box.submit()
            time.sleep(3)
            
            # Click target website
            target_link = driver.find_element(By.XPATH, f"//a[contains(@href, '{target_website}')]")
            target_link.click()
            time.sleep(3)
            
            # Scroll to bottom slowly
            self.slow_scroll(driver)
            
            # Back to top
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
            # Click random post/article
            links = driver.find_elements(By.TAG_NAME, "a")
            if links:
                random_link = random.choice(links)
                random_link.click()
                time.sleep(3)
                
                # Scroll for 20 seconds
                self.scroll_for_duration(driver, 20)
                
            return True
            
        except Exception as e:
            print(f"Visit simulation error: {e}")
            return False
    
    def slow_scroll(self, driver):
        total_height = driver.execute_script("return document.body.scrollHeight")
        for i in range(0, total_height, 50):
            driver.execute_script(f"window.scrollTo(0, {i});")
            time.sleep(0.1)
    
    def scroll_for_duration(self, driver, seconds):
        start_time = time.time()
        while time.time() - start_time < seconds:
            driver.execute_script("window.scrollBy(0, 100);")
            time.sleep(1)
    
    def clear_cache(self, driver):
        driver.execute_script("window.localStorage.clear();")
        driver.execute_script("window.sessionStorage.clear();")
        driver.delete_all_cookies()
    
    def run_cycle(self, keywords, target_website, cycles=10):
        for cycle in range(cycles):
            print(f"Starting cycle {cycle + 1}/{cycles}")
            
            driver = self.setup_driver()
            if not driver:
                continue
                
            try:
                # IP leak check
                if not self.check_ip_leak(driver):
                    print("IP leak detected, skipping cycle")
                    continue
                
                # Google login
                self.google_login(driver)
                
                # Simulate visit
                keyword = random.choice(keywords)
                self.simulate_visit(driver, keyword, target_website)
                
                # Clear cache
                self.clear_cache(driver)
                
                print(f"Cycle {cycle + 1} completed successfully")
                
            except Exception as e:
                print(f"Cycle {cycle + 1} failed: {e}")
            finally:
                driver.quit()
            
            # Random delay between cycles
            time.sleep(random.randint(30, 60))

def main():
    booster = SEOTrafficBooster()
    
    # Configuration
    keywords = [
        "bitcoin untuk pemula",
        "apa itu cryptocurrecy",
        "technology news",
        "trading sinyal future",
        "harga bitcoin hari ini"
    ]
    
    target_website = "https://cryptoajah.blogspot.com"  # Replace with your website
    
    # Run cycles
    booster.run_cycle(keywords, target_website, cycles=10)

if __name__ == "__main__":
    main()
