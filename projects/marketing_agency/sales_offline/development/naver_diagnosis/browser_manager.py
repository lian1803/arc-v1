"""
브라우저 인스턴스 관리
크래시 감지 시 자동 재기동
"""
from playwright.async_api import Browser


async def launch_browser(playwright) -> Browser:
    """Chromium 브라우저 인스턴스를 띄운다."""
    return await playwright.chromium.launch(
        headless=True,
        args=[
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
        ],
    )


async def get_browser(app) -> Browser:
    """
    브라우저 인스턴스를 반환한다.
    크래시/연결 끊김이 감지되면 자동으로 재기동한다.
    """
    browser: Browser = app.state.browser
    try:
        if not browser.is_connected():
            raise RuntimeError("browser disconnected")
    except Exception:
        print("[BrowserRecovery] 브라우저 재기동 시도...")
        try:
            await browser.close()
        except Exception:
            pass
        app.state.browser = await launch_browser(app.state.playwright)
        print("[BrowserRecovery] 브라우저 재기동 완료")
        browser = app.state.browser
    return browser
