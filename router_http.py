"""Browser-free access to the Netgear admin UI: form login, page fetch, radio state."""

import base64
import http.cookiejar
import random
import re
import ssl
import string
import urllib.parse
import urllib.request


class RouterHTTP:
    """One admin session over plain HTTP(S). Each instance logs in fresh."""

    def __init__(self, base_url: str, username: str, password: str, timeout: int = 10):
        self.base = base_url.rstrip("/")
        self.username, self.password, self.timeout = username, password, timeout
        self.jar = http.cookiejar.CookieJar()
        ctx = ssl.create_default_context()
        ctx.check_hostname, ctx.verify_mode = False, ssl.CERT_NONE  # router uses a self-signed cert
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.jar), urllib.request.HTTPSHandler(context=ctx))

    def _open(self, path: str, data: dict = None) -> str:
        body = urllib.parse.urlencode(data).encode() if data else None
        with self.opener.open(urllib.request.Request(self.base + path, data=body), timeout=self.timeout) as r:
            return r.read().decode(errors="ignore")

    @staticmethod
    def _is_login_page(html: str) -> bool:
        return 'name="username"' in html and "checklogin" in html

    def _encode_password(self) -> str:
        # Mirrors the login page's checklogin(): base64(rand + base64(pw) + rand)
        pad = string.digits + string.ascii_letters + "="
        inner = base64.b64encode(self.password.encode()).decode()
        return base64.b64encode((random.choice(pad) + inner + random.choice(pad)).encode()).decode()

    def login(self) -> None:
        page = self._open("/")
        if not self._is_login_page(page):
            return
        ts = re.search(r'timestamp=(\d+)', page) or re.search(r'var ts\s*=\s*"(\d+)"', page)
        result = self._open("/apply.cgi?%20timestamp=" + (ts.group(1) if ts else ""), {
            "submit_flag": "admin_login", "username": self.username, "password": self._encode_password()})
        if self._is_login_page(self._open("/WLG_adv.htm")):
            raise RuntimeError(f"Router login rejected (code {result.strip()[:8]!r}: 3=another admin session, 5=bad credentials)")

    def get(self, page: str) -> str:
        return self._open("/" + page.lstrip("/"))

    def radio_enabled(self) -> bool:
        """2.4 GHz radio state as saved on the router (WLG_adv.htm's con_endis_wl_radio)."""
        m = re.search(r"var con_endis_wl_radio\s*=\s*'(\d)'", self.get("WLG_adv.htm"))
        if not m:
            raise RuntimeError("Radio state not found on WLG_adv.htm (firmware UI changed?)")
        return m.group(1) == "1"

    def cookies(self) -> list:
        return [{"name": c.name, "value": c.value, "path": c.path or "/"} for c in self.jar]
