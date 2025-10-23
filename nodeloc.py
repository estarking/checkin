# -*- coding:utf-8 -*-
# -------------------------------
# @Author : github@wh1te3zzz
# @Time   : 2025-09-01
# NodeLoc 签到脚本（支持Telegram推送）
# -------------------------------

"""
NodeLoc签到
自行网页捉包提取请求头中的cookie和x-csrf-token填到变量 NL_COOKIE 中,用#号拼接，多账号换行隔开
export NL_COOKIE="_t=******; _forum_session=xxxxxx#XXXXXX"
export TG_BOT_TOKEN="你的BotToken"
export TG_USER_ID="你的UserID"

cron: 59 8 * * *
"""
import os
import time
import logging
import threading
from datetime import datetime
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import requests

# ==================== 固定配置 ====================
DOMAIN = "www.nodeloc.com"
HOME_URL = f"https://{DOMAIN}/u/"  # 用户列表页
CHECKIN_BUTTON_SELECTOR = 'li.header-dropdown-toggle.checkin-icon button.checkin-button'
USERNAME_SELECTOR = 'div.directory-table__row.me a[data-user-card]'  # 当前登录用户
SCREENSHOT_DIR = "./photo"
LOG_LEVEL = logging.INFO
# ===================================================
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
log = logging.getLogger(__name__)
results = []

# ==================== Telegram 推送 ====================
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "")
TG_USER_ID = os.getenv("TG_USER_ID", "")
TG_API_HOST = os.getenv("TG_API_HOST", "https://api.telegram.org")

def telegram_bot(title: str, content: str):
    if not TG_BOT_TOKEN or not TG_USER_ID:
        print("❌ Telegram 配置未设置，跳过推送")
        return
    url = f"{TG_API_HOST}/bot{TG_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TG_USER_ID,
        "text": f"{title}\n\n{content}",
        "parse_mode": "HTML"
    }
    try:
        resp = requests.post(url, data=data, timeout=10)
        if resp.status_code == 200:
            print(f"✅ Telegram 推送成功: {title}")
        else:
            print(f"❌ Telegram 推送失败: {resp.text}")
    except Exception as e:
        print(f"❌ Telegram 推送异常: {e}")

def send(title: str, content: str):
    t = threading.Thread(target=telegram_bot, args=(title, content))
    t.start()
    t.join()
# ===================================================

def generate_screenshot_path(prefix: str) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    return os.path.join(SCREENSHOT_DIR, f"{prefix}_{ts}.png")

def get_username_from_user_page(driver) -> str:
    log.debug("🔍 正在提取用户名...")
    try:
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, USERNAME_SELECTOR))
        )
        username = element.get_attribute("data-user-card")
        return username.strip() if username else "未知用户"
    except Exception as e:
        log.error(f"❌ 提取用户名失败: {e}")
        return "未知用户"

def check_login_status(driver):
    log.debug("🔐 正在检测登录状态...")
    try:
        WebDriverWait(driver, 10).until(
            EC.any_of(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.directory-table__row.me")),
                EC.presence_of_element_located((By.CSS_SELECTOR, "button.checkin-button"))
            )
        )
        log.info("✅ 登录成功")
        return True
    except Exception as e:
        log.error(f"❌ 登录失败或 Cookie 无效: {e}")
        screenshot_path = generate_screenshot_path('login_failed')
        driver.save_screenshot(screenshot_path)
        log.info(f"📸 已保存登录失败截图：{screenshot_path}")
        return False

def setup_browser():
    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-infobars')
    options.add_argument('--disable-popup-blocking')
    options.add_argument('--headless=new')
    log.debug("🌐 启动 Chrome（无头模式）...")
    try:
        driver = uc.Chrome(
            options=options,
            driver_executable_path=None,
            version_main=140,
            use_subprocess=True
        )
        driver.set_window_size(1920, 1080)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => false});")
        driver.execute_script("window.chrome = { runtime: {} };")
        driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});")
        driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh']});")
        return driver
    except Exception as e:
        log.error(f"❌ 浏览器启动失败: {e}")
        return None

def hover_checkin_button(driver):
    try:
        wait = WebDriverWait(driver, 10)
        button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, CHECKIN_BUTTON_SELECTOR)))
        ActionChains(driver).move_to_element(button).perform()
        time.sleep(1)
    except Exception as e:
        log.warning(f"⚠️ 刷新签到状态失败: {e}")

def perform_checkin(driver, username: str):
    try:
        driver.get(HOME_URL)
        time.sleep(3)
        hover_checkin_button(driver)
        wait = WebDriverWait(driver, 10)
        button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, CHECKIN_BUTTON_SELECTOR)))

        if "checked-in" in button.get_attribute("class"):
            msg = f"[✅] {username} 今日已签到"
            log.info(msg)
            return msg

        log.info(f"📌 {username} - 准备签到")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", button)
        time.sleep(3)

        hover_checkin_button(driver)

        if "checked-in" in button.get_attribute("class"):
            msg = f"[🎉] {username} 签到成功！"
            log.info(msg)
            return msg
        else:
            msg = f"[⚠️] {username} 点击后状态未更新，可能失败"
            log.warning(msg)
            path = generate_screenshot_path("checkin_uncertain")
            driver.save_screenshot(path)
            log.info(f"📸 已保存状态存疑截图：{path}")
            return msg

    except Exception as e:
        msg = f"[❌] {username} 签到异常: {e}"
        log.error(msg)
        path = generate_screenshot_path("checkin_error")
        try:
            driver.save_screenshot(path)
            log.info(f"📸 已保存错误截图：{path}")
        except:
            pass
        return msg

def process_account(cookie_str: str):
    cookie = cookie_str.split("#", 1)[0].strip()
    if not cookie:
        msg = "[❌] Cookie 为空"
        send("NodeLoc签到失败", msg)
        return msg

    driver = None
    try:
        driver = setup_browser()
        if not driver:
            msg = "[❌] 浏览器启动失败"
            send("NodeLoc签到失败", msg)
            return msg

        log.info("🚀 正在打开用户列表页...")
        driver.get(HOME_URL)
        time.sleep(3)

        for item in cookie.split(";"):
            item = item.strip()
            if not item or "=" not in item:
                continue
            try:
                name, value = item.split("=", 1)
                driver.add_cookie({
                    'name': name.strip(),
                    'value': value.strip(),
                    'domain': '.nodeloc.com',
                    'path': '/',
                    'secure': True,
                    'httpOnly': False
                })
            except Exception as e:
                log.warning(f"[⚠️] 添加 Cookie 失败: {item} -> {e}")
                continue

        driver.refresh()
        time.sleep(5)

        if not check_login_status(driver):
            msg = "[❌] 登录失败，Cookie 可能失效"
            send("NodeLoc签到失败", msg)
            return msg

        username = get_username_from_user_page(driver)
        log.info(f"👤 当前用户: {username}")

        result = perform_checkin(driver, username)

        if "成功" in result or "已签到" in result:
            send("NodeLoc签到成功", result)
        else:
            send("NodeLoc签到失败", result)

        return result

    except Exception as e:
        msg = f"[🔥] 处理异常: {e}"
        log.error(msg)
        send("NodeLoc签到异常", msg)
        return msg
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

def main():
    global results
    if 'NL_COOKIE' not in os.environ:
        msg = "❌ 未设置 NL_COOKIE 环境变量"
        print(msg)
        results.append(msg)
        send("NodeLoc签到失败", msg)
        return

    raw_lines = os.environ.get("NL_COOKIE").strip().split("\n")
    cookies = [line.strip() for line in raw_lines if line.strip()]

    if not cookies:
        msg = "❌ 未解析到有效 Cookie"
        print(msg)
        results.append(msg)
        send("NodeLoc签到失败", msg)
        return

    log.info(f"✅ 查找到 {len(cookies)} 个账号，开始顺序签到...")

    for cookie_str in cookies:
        result = process_account(cookie_str)
        results.append(result)
        time.sleep(5)

    log.info("✅ 全部签到完成")

if __name__ == '__main__':
    main()
