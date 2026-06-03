"""
mavis.skills.whatsapp — WhatsApp Web via Playwright (sessão persistente).
LEITURA de mensagens não-lidas e ENVIO por contato/grupo.
Desktop-only (precisa navegador visual + sessão).
"""
import os
import time
from typing import List, Dict, Any, Optional

SESSAO = os.environ.get("WHATSAPP_SESSION_DIR", "sessao_whatsapp")
URL = "https://web.whatsapp.com"


def _launch():
    from playwright.sync_api import sync_playwright
    p = sync_playwright().start()
    ctx = p.chromium.launch_persistent_context(
        SESSAO,
        headless=False,
        args=["--start-maximized"],
        no_viewport=True,
    )
    page = ctx.new_page() if not ctx.pages else ctx.pages[0]
    page.goto(URL)
    return p, ctx, page


def list_unread(limit: int = 10) -> List[Dict[str, Any]]:
    """Lista chats com mensagens não-lidas."""
    p = ctx = page = None
    try:
        p, ctx, page = _launch()
        page.wait_for_selector("div[role='grid']", timeout=60000)
        time.sleep(3)
        items = page.query_selector_all("span[aria-label*='não lida'], span[aria-label*='unread']")
        out = []
        for el in items[:limit]:
            chat = el.evaluate(
                "node => { let p = node.closest('div[role=\"listitem\"]'); "
                "if (!p) return null; let title = p.querySelector('span[title]'); "
                "return title ? title.getAttribute('title') : null; }"
            )
            if chat:
                out.append({"chat": chat, "unread_label": el.get_attribute("aria-label")})
        return out
    except Exception as e:
        return [{"error": str(e)}]
    finally:
        try:
            if ctx:
                ctx.close()
            if p:
                p.stop()
        except Exception:
            pass


def send_message(contact: str, message: str) -> Dict[str, Any]:
    """Envia mensagem para contato/grupo por nome exato."""
    p = ctx = page = None
    try:
        p, ctx, page = _launch()
        page.wait_for_selector("div[role='grid']", timeout=60000)
        # Caixa de busca
        search = page.wait_for_selector("div[contenteditable='true'][data-tab='3']", timeout=20000)
        search.click()
        page.keyboard.type(contact, delay=30)
        time.sleep(1.5)
        page.keyboard.press("Enter")
        time.sleep(2)
        box = page.wait_for_selector("div[contenteditable='true'][data-tab='10']", timeout=15000)
        box.click()
        for line in message.split("\n"):
            page.keyboard.type(line, delay=15)
            page.keyboard.press("Shift+Enter")
        # Remove o último Shift+Enter e envia
        page.keyboard.press("Backspace")
        page.keyboard.press("Enter")
        time.sleep(2)
        return {"ok": True, "to": contact, "message": message}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        try:
            if ctx: ctx.close()
            if p: p.stop()
        except Exception:
            pass
