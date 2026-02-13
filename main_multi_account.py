# main_multi_account.py
import os
import time
import re
import sys
from DrissionPage import ChromiumPage, ChromiumOptions
from DrissionPage import Chromium
import random
import argparse
import json

chrome_candidates = [
    "/opt/google/chrome/chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/usr/lib/chromium/chromium",
    "/usr/lib/chromium-browser/chromium-browser",
    "/snap/bin/chromium",
    "/snap/bin/chromium-browser",
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/usr/local/bin/chromium",
    "/usr/local/bin/chromium-browser",
    "/usr/bin/microsoft-edge-stable",
    "/opt/microsoft/msedge/msedge"
]

binpath = next((path for path in chrome_candidates if os.path.exists(path)), None)
cwd = os.getcwd()

if binpath:
    print(f"✅ 找到浏览器路径: {binpath}")
else:
    print("⚠️ 警告: 未找到浏览器可执行文件，将使用系统默认路径")
    binpath = None

parser = argparse.ArgumentParser(description="weridhost续期")
parser.add_argument('-k', '--keep', action='store_true', help='启用保留模式')
parser.add_argument('-d', '--debug', action='store_true', help='启用调试模式')
iargs = parser.parse_args()

def safe_ele(obj, selector, timeout=5):
    try:
        return obj.ele(selector, timeout=timeout)
    except:
        return None

def safe_shadow_root(ele):
    try:
        return ele.shadow_root
    except:
        return None

def safe_get_frame(shadow, index):
    try:
        return shadow.get_frame(index)
    except:
        return None

def solve_turnstile(page):
    print('waiting for turnstile')
    div = safe_ele(page, 'xpath://*[@id="app"]/div[2]/div/div[2]/div[2]/section/div[1]/div[3]/div[1]/div/div[3]/div[2]/div/div[1]', 15)
    if not div:
        div = safe_ele(page, 'xpath://*[@id="app"]/div[2]/div/div[2]/div[2]/div/div/div/div[2]/div/div[1]', 15)
        print(f'✅ 发现游戏机超过续期时间')
    else:
        print(f'✅ 游戏机在续期时间内')
    div2 = safe_ele(div, 'tag:div', 5)
    div3 = safe_ele(div2, 'tag:div', 5)
    shadow = safe_shadow_root(div3)
    iframe1 = safe_get_frame(shadow, 1)
    body = safe_ele(iframe1, 'tag:body', 5)
    shadow2 = safe_shadow_root(body)
    checkbox = safe_ele(shadow2, 'tag:input', 5)

    if iargs.debug:
        for name, ele in [('div最外层', div), ('div2', div2), ('div3', div3),
                          ('iframe', iframe1), ('body', body), ('shadow2', body), ('checkbox', checkbox)]:
            check_element(name, ele)
    else:
        for name, ele in [('div最外层', div), ('div2', div2), ('div3', div3),
                          ('iframe', iframe1), ('body', body), ('checkbox', checkbox)]:
            if ele is None:
                check_element(name, ele)
                break

    if checkbox:
        xof = random.randint(5, 8)
        yof = random.randint(5, 8)
        capture_screenshot("when_cf_turnstile1.png", page=page)
        checkbox.offset(x=xof, y=yof).click(by_js=False)
        print(f'✅ 找到并点击turnstile')
        time.sleep(1)
        capture_screenshot("when_cf_turnstile2.png", page=page)
        return True
    return False

def check_action_success(page):
    success = page.ele("x://h2[contains(text(), '성공!')]", timeout=10)
    if success:
        print("✅ 续期成功")
        return True
    h2 = page.ele("x://h2[contains(., '아직')]", timeout=5)
    error_found = page.ele("x://div[@type='error']", timeout=10)
    if h2 or error_found:
        print("⚠️ 未到续期时间。")
        return False
    print("⚠️ 按钮已点击，但未检测到明确的成功或错误提示。")
    return False

def capture_screenshot(file_name=None, save_dir='screenshots', page=None, account_name=""):
    os.makedirs(save_dir, exist_ok=True)
    if not file_name:
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_name = f'screenshot_{timestamp}.png'
    if account_name:
        name, ext = os.path.splitext(file_name)
        file_name = f"{name}_{account_name}{ext}"
    full_path = os.path.join(save_dir, file_name)
    try:
        page.get_screenshot(path=save_dir, name=file_name, full_page=True)
        print(f"📸 截图已保存：{full_path}")
    except Exception as e:
        print(f"⚠️ 截图失败: {e}")

def check_element(desc, element, exit_on_fail=True):
    if element:
        print(f'✓ {desc}: {element}')
        return True
    else:
        print(f'✗ {desc}: 获取失败')
        return False

def search_btn(page):
    add_button_txt = "시간추가"
    print(f"🔍 正在查找 '{add_button_txt}' 按钮...")
    try:
        page.wait.ele_displayed('//div[contains(@class, "RenewBox2")]', timeout=10)
    except:
        print("⚠️ 等待 RenewBox2 容器超时，继续尝试查找...")

    selectors = [
        '//button[@color="primary"]',
        '//button[contains(@class, "Button__ButtonStyle-sc-1qu1gou-0")]',
        '//div[contains(@class, "RenewBox2")]//button[1]',
        f'//button[contains(text(), "{add_button_txt}")]',
        '//button[contains(., "시간")]',
    ]
    for i, selector in enumerate(selectors, 1):
        try:
            btn = page.ele(selector, timeout=3)
            if btn:
                print(f"✅ 通过选择器 #{i} 找到按钮: {selector}")
                return btn
        except:
            continue
    print(f"❌ 未找到 '{add_button_txt}' 按钮（已尝试 {len(selectors)} 种方法）")
    return None

def add_server_time(account_config, account_index=1):
    """为单个账号添加服务器时间"""
    server_url = account_config.get('server_url', '')
    remember_web_cookie = account_config.get('cookie', '')
    chrome_proxy = account_config.get('proxy', '')
    account_name = account_config.get('name', f'Account{account_index}')

    print(f"\n{'='*60}")
    print(f"🚀 开始处理账号 #{account_index}: {account_name}")
    print(f"{'='*60}")

    if not server_url or not remember_web_cookie:
        error = '缺少服务器URL' if not server_url else '缺少Cookie'
        print(f"❌ 账号 {account_name}: {error}")
        return {'name': account_name, 'success': False, 'error': error}

    print(f"📌 服务器URL: {server_url}")
    print(f"🔐 Cookie: {remember_web_cookie[:20]}...")
    if chrome_proxy:
        print(f"🌐 代理: {chrome_proxy}")

    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    browser = None
    page = None

    # 每个账号使用不同的调试端口，避免冲突
    debug_port = 9222 + account_index

    try:
        options = (
            ChromiumOptions()
            .set_user_agent(user_agent)
            .set_argument('--guest')
            .set_argument('--no-sandbox')
            .set_argument('--disable-gpu')
            .set_argument('--window-size=1280,800')
            .set_argument('--disable-dev-shm-usage')
            .set_argument(f'--user-data-dir={cwd}/.tmp_{account_index}')
            .set_argument('--disable-software-rasterizer')
            .set_browser_path(binpath)
            .set_local_port(debug_port)
        )

        if chrome_proxy:
            options.set_argument(f'--proxy-server={chrome_proxy}')

        if 'DISPLAY' not in os.environ:
            options.headless(True)
            print("✅ 无头模式")
        else:
            options.headless(False)
            print("✅ 正常模式")

        print(f"正在为账号 {account_name} 启动浏览器 (端口: {debug_port})...")
        browser = Chromium(options)
        print(f"✅ 浏览器启动成功")

        page = browser.latest_tab

        # Cookie 登录
        print(f"尝试使用 Cookie 登录...")
        try:
            page.set.cookies.clear()
            page.set.cookies({
                'name': 'pterodactyl_session',
                'value': remember_web_cookie.strip(),
                'path': '/',
                'domain': 'hub.weirdhost.xyz'
            })
            page.get(server_url)
            page.wait.load_start()
            time.sleep(3)

            if "login" in page.url or "auth" in page.url:
                print(f"❌ Cookie 登录失败")
                capture_screenshot("login_fail.png", page=page, account_name=account_name)
                return {'name': account_name, 'success': False, 'error': 'Cookie登录失败'}
            print(f"✅ Cookie 登录成功")
        except Exception as e:
            print(f"Cookie 登录出错: {e}")
            return {'name': account_name, 'success': False, 'error': f'登录异常: {e}'}

        # 确保在正确页面
        if server_url not in page.url:
            page.get(server_url)
            page.wait.load_start()
            time.sleep(3)
            if "login" in page.url.lower():
                print(f"❌ 导航失败，会话可能失效")
                capture_screenshot("nav_fail.png", page=page, account_name=account_name)
                return {'name': account_name, 'success': False, 'error': '登录失败'}

        print(f"✅ 已进入服务器页面: {page.url}")

        # 查找并点击按钮
        btn = search_btn(page)
        if not btn:
            capture_screenshot("btn_not_found.png", page=page, account_name=account_name)
            return {'name': account_name, 'success': False, 'error': '未找到续期按钮'}

        if not btn.states.is_enabled:
            return {'name': account_name, 'success': False, 'error': '按钮不可点击'}

        print(f"✅ 按钮已找到且可点击")
        try:
            if not btn.states.is_displayed:
                page.scroll.to_see(btn)
                time.sleep(1)
        except:
            pass

        # Turnstile 验证重试
        for attempt in range(1, 4):
            print(f"\n🔄 [尝试 {attempt}/3]")
            try:
                btn.click(by_js=False)
                print(f"✅ 点击 '시간 추가' 按钮")
            except Exception as e:
                print(f"❌ 点击按钮失败: {e}")
                if attempt < 3:
                    time.sleep(3)
                continue

            time.sleep(5)
            try:
                if solve_turnstile(page):
                    break
                print(f"⚠️ Turnstile 验证未通过")
            except Exception as e:
                print(f"❌ Turnstile 异常: {e}")

            if attempt < 3:
                time.sleep(3)
            else:
                print(f"❌ Turnstile 验证失败：已达最大重试次数")

        time.sleep(5)
        action_success = check_action_success(page)
        capture_screenshot("result.png", page=page, account_name=account_name)

        if action_success:
            print(f"✅ 账号 {account_name} 续期成功！")
            return {'name': account_name, 'success': True}
        else:
            return {'name': account_name, 'success': False, 'error': '未到续期时间或操作失败'}

    except Exception as e:
        print(f"❌ 账号 {account_name} 执行错误: {e}")
        import traceback
        traceback.print_exc()
        if page:
            try:
                capture_screenshot("error.png", page=page, account_name=account_name)
            except:
                pass
        return {'name': account_name, 'success': False, 'error': str(e)}

    finally:
        if browser:
            try:
                browser.quit()
                time.sleep(2)
                print(f"✅ 账号 {account_name} 浏览器已关闭")
            except Exception as e:
                print(f"⚠️ 关闭浏览器出错: {e}")
        # 清理临时目录
        import shutil
        tmp_dir = f'{cwd}/.tmp_{account_index}'
        if os.path.exists(tmp_dir):
            try:
                shutil.rmtree(tmp_dir)
            except:
                pass

def load_accounts():
    """
    从环境变量加载账号配置
    
    支持三种格式:
    1. ACCOUNTS_JSON: JSON数组，多账号
    2. ACCOUNT_1, ACCOUNT_2, ...: 每个是JSON对象
    3. WEIRDHOST_SERVER_URLS + REMEMBER_WEB_COOKIE: 单账号兼容
    """
    accounts = []

    # 方式1: ACCOUNTS_JSON
    accounts_json = os.environ.get('ACCOUNTS_JSON', '')
    if accounts_json:
        try:
            accounts = json.loads(accounts_json)
            print(f"📋 从 ACCOUNTS_JSON 加载了 {len(accounts)} 个账号")
            return accounts
        except json.JSONDecodeError as e:
            print(f"❌ 解析 ACCOUNTS_JSON 失败: {e}")
            sys.exit(1)

    # 方式2: ACCOUNT_1, ACCOUNT_2, ...
    i = 1
    while True:
        acc_str = os.environ.get(f'ACCOUNT_{i}', '')
        if not acc_str:
            break
        try:
            acc = json.loads(acc_str)
            if 'name' not in acc:
                acc['name'] = f'Account_{i}'
            accounts.append(acc)
        except json.JSONDecodeError as e:
            print(f"⚠️ 解析 ACCOUNT_{i} 失败: {e}")
        i += 1

    if accounts:
        print(f"📋 从 ACCOUNT_N 环境变量加载了 {len(accounts)} 个账号")
        return accounts

    # 方式3: 单账号兼容
    server_url = os.environ.get('WEIRDHOST_SERVER_URLS', '')
    cookie = os.environ.get('REMEMBER_WEB_COOKIE', '')
    proxy = os.environ.get('PROXY', '')
    if server_url and cookie:
        print("📋 使用单账号模式（兼容旧格式）")
        return [{'name': 'Default Account', 'server_url': server_url, 'cookie': cookie, 'proxy': proxy}]

    print("❌ 未找到账号配置！")
    print("请设置以下环境变量之一：")
    print("  1. ACCOUNTS_JSON - JSON数组")
    print('     例: [{"name":"acc1","server_url":"...","cookie":"...","proxy":""}]')
    print("  2. ACCOUNT_1, ACCOUNT_2, ... - 每个是JSON对象")
    print("  3. WEIRDHOST_SERVER_URLS + REMEMBER_WEB_COOKIE - 单账号")
    sys.exit(1)

def save_results(results):
    try:
        with open('results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print("📝 结果已保存到 results.json")
    except Exception as e:
        print(f"⚠️ 保存结果失败: {e}")

def main():
    print(f"\n{'#'*60}")
    print(f"# WeirdHost 多账号自动续期脚本")
    print(f"{'#'*60}\n")

    try:
        accounts = load_accounts()
        print(f"📊 共需处理 {len(accounts)} 个账号\n")

        results = []
        for index, account in enumerate(accounts, 1):
            result = add_server_time(account, index)
            results.append(result)
            if index < len(accounts):
                wait_time = 5
                print(f"\n⏳ 等待 {wait_time} 秒后处理下一个账号...\n")
                time.sleep(wait_time)

        # 汇总
        print(f"\n{'='*60}")
        print(f"📊 执行结果汇总")
        print(f"{'='*60}\n")

        success_count = sum(1 for r in results if r.get('success'))
        fail_count = len(results) - success_count

        for r in results:
            status = "✅ 成功" if r.get('success') else "❌ 失败"
            error = f" ({r.get('error', '')})" if r.get('error') else ""
            print(f"{status} - {r['name']}{error}")

        print(f"\n总计: {len(results)} | 成功: {success_count} | 失败: {fail_count}\n")
        save_results(results)

        if not iargs.keep:
            sys.exit(0 if fail_count == 0 else (1 if success_count == 0 else 2))

    except KeyboardInterrupt:
        print("\n⚠️ 用户中断执行")
        if not iargs.keep:
            sys.exit(130)
    except Exception as e:
        print(f"❌ 未捕获的异常: {e}")
        import traceback
        traceback.print_exc()
        if not iargs.keep:
            sys.exit(1)

if __name__ == "__main__":
    if iargs.debug:
        print("⚠️ Debug模式未实现多账号支持")
        sys.exit(1)
    else:
        main()