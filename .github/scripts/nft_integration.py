"""Integration-only real nftables test; use a disposable VM, never a production host."""
import concurrent.futures
import http.cookiejar
import json
import sys
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:18082"
COUNT = 400_000


def generate():
    with open("/tmp/niftywall-ci.nft", "w", encoding="utf-8") as f:
        f.write("add table ip nw_ci\n")
        f.write("add set ip nw_ci large_set { type ipv4_addr; size 500000; }\n")
        elements = (f"10.{i >> 16}.{(i >> 8) & 255}.{i & 255}" for i in range(COUNT))
        f.write("add element ip nw_ci large_set { " + ", ".join(elements) + " }\n")


def verify():
    jar = http.cookiejar.CookieJar()
    client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    def post(path, data):
        return client.open(BASE + path, urllib.parse.urlencode(data).encode(), timeout=30)
    assert client.open(BASE + "/onboarding", timeout=10).status == 200
    with post("/onboarding", {"username": "ciadmin", "password": "temporary-test-password"}) as response:
        assert response.status == 200
    with post("/login", {"username": "ciadmin", "password": "temporary-test-password"}) as response:
        assert response.status == 200
    def fetch():
        with client.open(BASE + "/api/ruleset", timeout=120) as response:
            assert response.headers.get_content_type() == "application/json"
            raw = response.read()
        payload = json.loads(raw)
        assert isinstance(payload.get("nftables"), list)
        assert len(raw) >= 4_000_000, f"ruleset too small: {len(raw)} bytes"
        assert any(item.get("set", {}).get("name") == "large_set" for item in payload["nftables"])
        print(f"Verified JSON ruleset: {len(raw)} bytes")
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        task = pool.submit(fetch)
        with urllib.request.urlopen(BASE + "/healthz", timeout=10) as response:
            assert json.load(response) == {"status": "ok"}
        task.result(timeout=125)
    with client.open(BASE + "/api/ruleset/sets", timeout=120) as response:
        assert response.headers.get_content_type() == "application/json"
        payload = json.load(response)
        assert isinstance(payload.get("nftables"), list)
        assert any(item.get("set", {}).get("name") == "large_set" for item in payload["nftables"])
    print("Authenticated set listing and health check passed")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("generate", "verify"):
        raise SystemExit("Expected generate or verify")
    globals()[sys.argv[1]]()
