"""Check reachability of registered sources on the default branch."""
from concurrent.futures import ThreadPoolExecutor
import ipaddress
import os
import socket
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from research import ROOT, SOURCE_FIELDS, rows, valid_https


def public_https(url):
    if not valid_https(url):
        raise ValueError("Expected a public HTTPS source")
    host = urlsplit(url).hostname
    addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
        raise ValueError("Source resolved to a non-public address")
    return host


class PublicRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        public_https(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def check_url(opener, request):
    for attempt in range(2):
        try:
            with opener.open(request, timeout=8) as response:
                return response.status
        except HTTPError as error:
            if error.code < 500 and error.code != 429:
                return error.code
            result = error.code
        except (URLError, TimeoutError, OSError, ValueError) as error:
            result = type(error).__name__
        if attempt == 0:
            time.sleep(1)
    return result


def check(source):
    sid, url = source["id"], source["url"]
    host = urlsplit(url).hostname
    agent = "Jensen-Huang-Research-Link-Check"
    if host and (host == "sec.gov" or host.endswith(".sec.gov")):
        contact = os.environ.get("SEC_CONTACT", "")
        if not contact:
            return sid, "REVIEW", "SEC_CONTACT is unset"
        agent += f" {contact}"
    try:
        public_https(url)
    except (OSError, ValueError) as error:
        return sid, "REVIEW", type(error).__name__
    opener = build_opener(PublicRedirects())
    status = check_url(opener, Request(url, method="HEAD", headers={"User-Agent": agent}))
    if status in {400, 403, 404, 405, 406, 410, 501}:
        status = check_url(opener, Request(url, headers={"User-Agent": agent}))
    if isinstance(status, int) and 200 <= status < 300:
        return sid, "OK", status
    return sid, "BROKEN" if status in {404, 410} else "REVIEW", status


def main():
    sources = rows(ROOT / "sources/registry.csv", SOURCE_FIELDS)
    with ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(check, sources))
    for sid, status, detail in results:
        print(f"{status:6} {sid} {detail}")
    if all(status != "OK" for _, status, _ in results):
        raise SystemExit("No source reachable. Check network or source access.")
    if any(status == "BROKEN" for _, status, _ in results):
        raise SystemExit("At least one registered URL returned 404 or 410 on GET.")


if __name__ == "__main__":
    main()
