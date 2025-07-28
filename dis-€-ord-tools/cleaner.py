import time
import os
import threading
import sys
import tls_client
import random
import datetime
import base64
import json
import websocket
from concurrent.futures import ThreadPoolExecutor, as_completed
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Configuration
MAX_RETRIES = 3
REQUEST_DELAY = (0.8, 1.5)
THREAD_LOCK = threading.Lock()
CONSOLE_LOCK = threading.Lock()

class TokenProcessor:
    _stats = {
        'total': 0,
        'cleaned': 0,
        'locked': 0,
        'invalid': 0,
        'failed': 0
    }
    
    @classmethod
    def update_stat(cls, stat, value=1):
        with CONSOLE_LOCK:
            cls._stats[stat] += value
            cls.update_title()
    
    @classmethod
    def update_title(cls):
        elapsed = time.strftime('%H:%M:%S', time.gmtime(time.time() - cls.start_time))
        title = (
            f"Discord Cleaner | "
            f"Total: {cls._stats['total']} | "
            f"Cleaned: {cls._stats['cleaned']} | "
            f"Locked: {cls._stats['locked']} | "
            f"Invalid: {cls._stats['invalid']} | "
            f"Failed: {cls._stats['failed']} | "
            f"Elapsed: {elapsed}"
        )
        sys.stdout.write(f"\33]0;{title}\a")
        sys.stdout.flush()
    
    @classmethod
    def print_status(cls, token, status, message, color=Fore.WHITE):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        short_token = token[:25] + '...' if len(token) > 28 else token
        print(f"{Fore.LIGHTBLACK_EX}{timestamp}{Style.RESET_ALL} | "
              f"{color}{short_token}{Style.RESET_ALL} | "
              f"{status}: {message}")

    def __init__(self, line):
        self.line = line.strip()
        parts = self.line.split(":")
        self.email = parts[0] if len(parts) > 0 else ""
        self.password = parts[1] if len(parts) > 1 else ""
        self.token = parts[3] if len(parts) > 3 else ""
        
        self.session = self.create_session()
        self.ws = None
        self.proxy = self.get_proxy()
        self.retries = 0

    def create_session(self):
        session = tls_client.Session(
            client_identifier="chrome_120",
            random_tls_extension_order=True
        )
        
        session.headers = {
            'authority': 'discord.com',
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'authorization': self.token,
            'content-type': 'application/json',
            'origin': 'https://discord.com',
            'sec-ch-ua': '"Chromium";v="120", "Not A(Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'x-debug-options': 'bugReporterEnabled',
            'x-discord-locale': 'en-US',
            'x-discord-timezone': 'UTC',
            'x-super-properties': base64.b64encode(json.dumps({
                "os": "Windows",
                "browser": "Chrome",
                "device": "",
                "system_locale": "en-US",
                "browser_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "browser_version": "120.0.0.0",
                "os_version": "10",
                "referrer": "",
                "referring_domain": "",
                "referrer_current": "",
                "referring_domain_current": "",
                "release_channel": "stable",
                "client_build_number": 9999,
                "client_event_source": None
            }).encode()).decode()
        }
        return session

    def get_proxy(self):
        if not PROXIES:
            return None
        proxy = random.choice(PROXIES)
        if '://' not in proxy:
            proxy = f'http://{proxy}'
        return {'http': proxy, 'https': proxy}

    def open_websocket(self):
        try:
            self.ws = websocket.WebSocket()
            self.ws.connect('wss://gateway.discord.gg/?v=9&encoding=json')
            
            payload = {
                "op": 2,
                "d": {
                    "token": self.token,
                    "properties": {
                        "os": "Windows",
                        "browser": "Chrome",
                        "device": "",
                        "system_locale": "en-US",
                        "browser_user_agent": self.session.headers['user-agent'],
                        "browser_version": "120.0.0.0",
                        "os_version": "10",
                        "referrer": "",
                        "referring_domain": "",
                        "referrer_current": "",
                        "referring_domain_current": "",
                        "release_channel": "stable",
                        "client_build_number": 9999,
                        "client_event_source": None
                    },
                    "presence": {
                        "status": "online",
                        "since": 0,
                        "activities": [],
                        "afk": False
                    }
                }
            }
            self.ws.send(json.dumps(payload))
            return True
        except Exception as e:
            self.print_status(self.token, "WebSocket", f"Connection failed: {str(e)}", Fore.YELLOW)
            return False

    def close_websocket(self):
        try:
            if self.ws and self.ws.connected:
                self.ws.close()
        except:
            pass

    def make_request(self, method, url, **kwargs):
        for attempt in range(MAX_RETRIES):
            try:
                response = getattr(self.session, method)(url, proxy=self.proxy, **kwargs)
                if response.status_code == 429:  # Rate limited
                    retry_after = response.json().get('retry_after', 2)
                    time.sleep(retry_after + random.uniform(0.1, 0.5))
                    continue
                return response
            except Exception as e:
                self.print_status(self.token, "Request", f"Attempt {attempt+1} failed: {str(e)}", Fore.YELLOW)
                time.sleep(random.uniform(*REQUEST_DELAY))
        return None

    def get_user_data(self):
        response = self.make_request('get', 'https://discord.com/api/v9/users/@me')
        if not response or response.status_code != 200:
            return None
        return response.json()

    def get_relationships(self):
        response = self.make_request('get', 'https://discord.com/api/v9/users/@me/relationships')
        return response.json() if response and response.status_code == 200 else []

    def get_guilds(self):
        response = self.make_request('get', 'https://discord.com/api/v9/users/@me/guilds')
        return response.json() if response and response.status_code == 200 else []

    def get_channels(self):
        response = self.make_request('get', 'https://discord.com/api/v9/users/@me/channels')
        return response.json() if response and response.status_code == 200 else []

    def remove_relationship(self, user_id):
        url = f'https://discord.com/api/v9/users/@me/relationships/{user_id}'
        response = self.make_request('delete', url)
        return response.status_code == 204 if response else False

    def leave_guild(self, guild_id):
        url = f'https://discord.com/api/v9/users/@me/guilds/{guild_id}'
        response = self.make_request('delete', url)
        return response.status_code == 204 if response else False

    def delete_channel(self, channel_id):
        url = f'https://discord.com/api/v9/channels/{channel_id}'
        response = self.make_request('delete', url)
        return response.status_code == 200 if response else False

    def process(self):
        try:
            # Verify token validity
            user_data = self.get_user_data()
            if not user_data:
                self.print_status(self.token, "Status", "Invalid token", Fore.RED)
                self.save_result("invalid.txt")
                TokenProcessor.update_stat('invalid')
                return

            # Check if token is locked
            billing_response = self.make_request('get', 'https://discord.com/api/v9/users/@me/billing/payment-sources')
            if billing_response and billing_response.status_code == 403:
                self.print_status(self.token, "Status", "Locked token", Fore.RED)
                self.save_result("locked.txt")
                TokenProcessor.update_stat('locked')
                return

            # Open websocket connection
            self.open_websocket()
            
            # Start cleaning process
            self.print_status(self.token, "Status", "Starting cleaning process", Fore.CYAN)
            
            # Get and process relationships
            relationships = self.get_relationships()
            self.print_status(self.token, "Relationships", f"Found {len(relationships)}", Fore.YELLOW)
            for rel in relationships:
                if self.remove_relationship(rel['id']):
                    time.sleep(random.uniform(*REQUEST_DELAY))

            # Get and process guilds
            guilds = self.get_guilds()
            self.print_status(self.token, "Guilds", f"Found {len(guilds)}", Fore.YELLOW)
            for guild in guilds:
                if not guild.get('owner', False):
                    if self.leave_guild(guild['id']):
                        time.sleep(random.uniform(*REQUEST_DELAY))

            # Get and process channels
            channels = self.get_channels()
            self.print_status(self.token, "Channels", f"Found {len(channels)}", Fore.YELLOW)
            for channel in channels:
                if self.delete_channel(channel['id']):
                    time.sleep(random.uniform(*REQUEST_DELAY))

            self.print_status(self.token, "Status", "Successfully cleaned", Fore.GREEN)
            self.save_result("cleaned.txt")
            TokenProcessor.update_stat('cleaned')

        except Exception as e:
            self.print_status(self.token, "Error", f"Processing failed: {str(e)}", Fore.RED)
            self.save_result("failed.txt")
            TokenProcessor.update_stat('failed')
        finally:
            self.close_websocket()

    def save_result(self, filename):
        with THREAD_LOCK:
            with open(filename, 'a', encoding='utf-8') as f:
                f.write(f"{self.line}\n")
            self.remove_from_input()

    def remove_from_input(self):
        with THREAD_LOCK:
            with open("tokens.txt", 'r', encoding='utf-8') as f:
                lines = f.readlines()
            with open("tokens.txt", 'w', encoding='utf-8') as f:
                for line in lines:
                    if line.strip() != self.line:
                        f.write(line)

def load_proxies():
    try:
        with open("proxies.txt", "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"{Fore.YELLOW}[!] proxies.txt not found. Continuing without proxies.{Fore.RESET}")
        return []

if __name__ == "__main__":
    # Load proxies
    PROXIES = load_proxies()
    
    # Load tokens
    try:
        with open("tokens.txt", "r", encoding="utf-8") as f:
            tokens = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"{Fore.RED}[!] tokens.txt not found!{Fore.RESET}")
        sys.exit(1)
    
    if not tokens:
        print(f"{Fore.RED}[!] No tokens found in tokens.txt!{Fore.RESET}")
        sys.exit(1)

    TokenProcessor._stats['total'] = len(tokens)
    TokenProcessor.start_time = time.time()
    
    print(f"\n{Fore.CYAN}Starting Discord Token Cleaner{Fore.RESET}")
    print(f"{Fore.LIGHTBLACK_EX}• Loaded {len(tokens)} tokens")
    print(f"• Loaded {len(PROXIES)} proxies")
    print(f"• Starting at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Get thread count
    try:
        thread_count = min(int(input(f"{Fore.CYAN}Enter thread count (1-100): {Fore.RESET}")), 100)
    except ValueError:
        thread_count = 5
    
    # Process tokens
    with ThreadPoolExecutor(max_workers=thread_count) as executor:
        futures = [executor.submit(TokenProcessor(token).process) for token in tokens]
        for future in as_completed(futures):
            pass  # We handle results within each processor
    
    # Final report
    print(f"\n{Fore.CYAN}Cleanup completed!{Fore.RESET}")
    print(f"{Fore.GREEN}• Cleaned: {TokenProcessor._stats['cleaned']}{Fore.RESET}")
    print(f"{Fore.RED}• Locked: {TokenProcessor._stats['locked']}")
    print(f"• Invalid: {TokenProcessor._stats['invalid']}")
    print(f"• Failed: {TokenProcessor._stats['failed']}{Fore.RESET}")
    print(f"\n{Fore.LIGHTBLACK_EX}Results saved in: cleaned.txt, locked.txt, invalid.txt, failed.txt")