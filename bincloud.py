# -*- coding:utf-8 -*-
# -------------------------------
# @Author : github@wh1te3zzz https://github.com/wh1te3zzz/checkin
# @Time : 2025-08-19 14:36:22
# 56IDC保号脚本
# -------------------------------
"""
56IDC 免费vps自动续期
变量为cookie，多账户换行隔开
export BC_COOKIES = "cf_clearance=******; WHMCS2jRk8YCjn7Sg=******"

cron: 0 */2 * * *
const $ = new Env("56IDC续期");
"""
import os
import time
import logging
import undetected_chromedriver as uc
from datetime import datetime
from urllib.parse import urljoin
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# ==================== 配置区 ====================

ENABLE_SCREENSHOT = os.environ.get("ENABLE_SCREENSHOT", "true").lower() == "true"
SCREENSHOT_DIR = os.environ.get("SCREENSHOT_DIR", "/ql/data/photo")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

if ENABLE_SCREENSHOT:
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    logging.debug(f"📁 截图将保存至: {SCREENSHOT_DIR}")

# ==================== 工具函数 ====================

def parse_cookies(cookies_str):
    """解析多行 Cookie 字符串为字典列表"""
    cookie_dicts = []
    for line in cookies_str.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
        cookies = {}
        for part in line.split(';'):
            part = part.strip()
            if '=' in part:
                key, value = part.split('=', 1)
                cookies[key.strip()] = value.strip()
        if cookies:
            cookie_dicts.append(cookies)
    return cookie_dicts

def take_screenshot(driver, name="screenshot"):
    """保存截图（带时间戳）"""
    if not ENABLE_SCREENSHOT or not driver:
        return
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{SCREENSHOT_DIR}/{name}_{timestamp}.png"
    try:
        driver.save_screenshot(filename)
        logging.info(f"📸 截图已保存: {filename}")
    except Exception as e:
        logging.error(f"❌ 截图失败: {e}")

# ==================== 安全操作封装 ====================

def safe_get(driver, url, timeout=15):
    """安全访问页面，等待加载完成"""
    try:
        driver.get(url)
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        return True
    except Exception as e:
        logging.error(f"❌ 页面加载失败: {url} | {e}")
        return False

def safe_scroll_to(driver, locator, timeout=10):
    """滚动到指定元素"""
    try:
        element = WebDriverWait(driver, timeout).until(EC.presence_of_element_located(locator))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        return element
    except TimeoutException:
        logging.warning(f"⚠️ 元素未找到，无法滚动: {locator}")
        return None

def safe_switch_to_iframe(driver, iframe_locator, timeout=20):
    """安全进入 iframe"""
    try:
        WebDriverWait(driver, timeout).until(EC.frame_to_be_available_and_switch_to_it(iframe_locator))
        logging.debug("✅ 成功进入 virtualizor_manager iframe")
        return True
    except TimeoutException:
        logging.error("❌ iframe 加载超时或不可用")
        return False

def get_visible_status(driver, status_ids):
    """使用 JS 检测真正可见的状态（基于 offsetWidth/Height）"""
    js = """
    const ids = %s;
    for (const id of ids) {
        const el = document.getElementById(id);
        if (el && el.offsetWidth > 0 && el.offsetHeight > 0) return id;
    }
    return null;
    """ % list(status_ids.keys())
    for _ in range(30):
        result = driver.execute_script(js)
        if result:
            return status_ids[result]
        time.sleep(1)
    return "⏱️ Timeout (状态未加载)"

def click_start_button(driver, timeout=10):
    """尝试点击启动按钮 #startcell"""
    try:
        start_btn = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.ID, "startcell"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", start_btn)
        driver.execute_script("arguments[0].click();", start_btn)
        logging.info("✅ 成功点击【启动】按钮")
        return True
    except TimeoutException:
        logging.warning("⚠️ 未找到【启动】按钮或不可点击")
        return False
    except Exception as e:
        logging.error(f"❌ 点击启动按钮失败: {e}")
        return False

# ==================== 主程序 ====================

def main():
    cookie_string = os.getenv('BC_COOKIES')
    if not cookie_string:
        logging.error("❌ 错误：环境变量 BC_COOKIES 未设置！")
        return

    cookies_list = parse_cookies(cookie_string)
    if not cookies_list:
        logging.error("❌ 错误：解析 BC_COOKIES 后未得到有效的 Cookie 信息。")
        return

    logging.info(f"✅ 已加载 {len(cookies_list)} 个账号的 Cookie")

    base_url = "https://56idc.net"

    for account_idx, cookies in enumerate(cookies_list, start=1):
        driver = None
        logging.info(f"{'='*50}")
        logging.info(f"正在处理第 {account_idx} 个账号...")
        logging.info(f"{'='*50}")

        # 浏览器配置
        options = uc.ChromeOptions()
        for arg in [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-extensions",
            "--disable-plugins-discovery",
            "--disable-blink-features=AutomationControlled",
            "--start-maximized",
            "--headless=new",
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0 Safari/537.36"
        ]:
            options.add_argument(arg)
        driver = None

        try:
            # 启动浏览器
            driver = uc.Chrome(
                options=options,
                driver_executable_path='/usr/bin/chromedriver',
                version_main=138,
                use_subprocess=True
            )

            # 注入防检测脚本
            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                Object.defineProperty(navigator, 'webdriver', { get: () => false });
                window.navigator.chrome = { runtime: {} };
                Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
                """
            })

            # 登录主站
            if not safe_get(driver, f"{base_url}/clientarea.php?language=english"):
                take_screenshot(driver, f"login_failed_{account_idx}")
                continue

            # 注入 Cookie
            driver.delete_all_cookies()
            for name, value in cookies.items():
                driver.add_cookie({
                    'name': name,
                    'value': value,
                    'domain': '.56idc.net',
                    'path': '/',
                    'secure': True,
                    'httpOnly': False
                })

            # 重新加载
            if not safe_get(driver, f"{base_url}/clientarea.php?language=english"):
                take_screenshot(driver, f"reload_failed_{account_idx}")
                continue

            # 获取用户名
            try:
                username = WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, "a.dropdown-toggle .active-client span.item-text"))
                ).text.strip()
                logging.info(f"✅ 登录成功，当前用户：{username}")
            except Exception:
                logging.error("❌ 登录失败：未找到用户名")
                take_screenshot(driver, f"login_failed_{account_idx}")
                continue

            # 提取产品列表
            try:
                panel = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@menuitemname='Active Products/Services']"))
                )
                list_group = panel.find_element(By.CLASS_NAME, "list-group")
                items = list_group.find_elements(By.CLASS_NAME, "list-group-item")
            except Exception as e:
                logging.error(f"❌ 未找到产品列表: {e}")
                take_screenshot(driver, f"products_failed_{account_idx}")
                continue

            products = []
            for item in items:
                try:
                    content = item.find_element(By.CLASS_NAME, "list-group-item-content")
                    name_div = item.find_element(By.CLASS_NAME, "list-group-item-name")
                    href = content.get_attribute("data-href")
                    if not href:
                        continue

                    # 提取服务名
                    try:
                        prefix = name_div.find_element(By.TAG_NAME, "b").text.strip()
                    except:
                        prefix = ""
                    spans = name_div.find_elements(By.TAG_NAME, "span")
                    other = spans[0].text.strip() if spans else ""
                    full_name = f"{prefix} - {other.replace(prefix, '', 1).strip(' -')}" if other else prefix

                    # 提取域名
                    try:
                        domain = name_div.find_element(By.CSS_SELECTOR, "span.text-domain").text.strip()
                    except:
                        domain = ""

                    products.append({
                        'name': full_name,
                        'domain': domain,
                        'url': urljoin(base_url, href)
                    })
                except Exception as e:
                    logging.warning(f"⚠️ 跳过无效产品项: {e}")
                    continue

            logging.info(f"📊 检测到 {len(products)} 个已激活服务")

            # === 遍历产品检查 VPS 状态并自动启动 ===
            for i, product in enumerate(products, 1):
                logging.debug(f"➡️ 正在检查服务 [{i}/{len(products)}]: {product['name']} | 主机名: {product['domain']}")

                if not safe_get(driver, product['url']):
                    continue

                # 滚动到 Primary IP
                safe_scroll_to(driver, (By.XPATH, "//span[@class='list-info-title' and text()='Primary IP']"))

                # 进入 iframe
                if not safe_switch_to_iframe(driver, (By.ID, "virtualizor_manager")):
                    driver.switch_to.default_content()
                    continue

                # 检测状态
                status_map = {
                    'vm_status_online': '🟢 Online',
                    'vm_status_offline': '🔴 Offline',
                    'vm_status_suspended': '🟡 Suspended',
                    'vm_status_nw_suspended': '🟠 Network Suspended'
                }
                status = get_visible_status(driver, status_map)
                logging.info(f"📊 【VPS 状态】{product['domain']} | {status}")

                # 如果是 Offline，尝试启动
                if "Offline" in status:
                    logging.info("🔧 检测到 VPS 已关机，正在尝试启动...")
                    if click_start_button(driver):
                        logging.debug("🔄 已发送启动指令，等待状态刷新...")
                        time.sleep(5)  # 等待响应
                    else:
                        take_screenshot(driver, f"start_failed_{account_idx}_{i}")
                        logging.warning("⚠️ 启动操作失败，可能按钮被禁用或网络问题")

                # 返回主文档
                driver.switch_to.default_content()

        except Exception as e:
            logging.error(f"❌ 账号 {account_idx} 发生未预期错误: {e}")
            take_screenshot(driver, f"unexpected_error_{account_idx}")
        finally:
            if driver:
                try:
                    driver.quit()
                    logging.info(f"🔚 第 {account_idx} 个账号处理完成")
                except:
                    pass
            time.sleep(2)

    logging.info(f"{'='*50}")
    logging.info("✅ 所有账号处理完毕。")
    logging.info(f"{'='*50}")

# ==================== 启动 ====================

if __name__ == "__main__":
    main()
