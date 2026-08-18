import json
import urllib.error
import urllib.request


class ApiError(Exception):
    pass


class SimulatorApi:
    def __init__(self, base_url, secret, timeout=90):
        self.base_url = base_url.rstrip("/")
        self.secret = secret
        self.timeout = timeout

    def _post(self, path, payload, headers=None, raw_body=None):
        url = f"{self.base_url}{path}"
        body = raw_body.encode("utf-8") if raw_body is not None else json.dumps(payload).encode("utf-8")
        request_headers = {"Content-Type": "application/json"}
        if headers:
            request_headers = dict(headers)
        request = urllib.request.Request(url, data=body, headers=request_headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                text = response.read().decode("utf-8")
                status = response.status
        except urllib.error.HTTPError as error:
            text = error.read().decode("utf-8", errors="replace")
            raise ApiError(f"HTTP {error.code} {url}\n{text}") from error
        except urllib.error.URLError as error:
            raise ApiError(f"Không gọi được {url}: {error.reason}") from error

        if not text:
            return {"httpStatus": status}
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"httpStatus": status, "raw": text}

    def find_traces(self, short_id):
        return self._post(
            "/api/v2/shipping/simulation/traces",
            {"secret": self.secret, "shortId": short_id},
        )

    def save_scenario(self, shipping_id, entries):
        return self._post(
            "/api/v2/shipping/simulation/scenario",
            {"secret": self.secret, "shippingId": shipping_id, "entries": entries},
        )

    def clear_scenario(self, shipping_id):
        return self._post(
            "/api/v2/shipping/simulation/scenario/clear",
            {"secret": self.secret, "shippingId": shipping_id},
        )

    def build_webhook_request(self, shipping_id, entries):
        return self._post(
            "/api/v2/shipping/simulation/webhook-request",
            {"secret": self.secret, "shippingId": shipping_id, "entries": entries},
        )

    def send_webhook(self, webhook_request):
        return self._post(
            webhook_request["path"],
            None,
            headers=webhook_request["headers"],
            raw_body=webhook_request["body"],
        )
