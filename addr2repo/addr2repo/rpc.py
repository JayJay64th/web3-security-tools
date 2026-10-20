import requests


class RpcError(RuntimeError):
    pass


class Rpc:
    def __init__(self, url, timeout=30):
        self.url = url
        self.timeout = timeout
        self._id = 0

    def call(self, method, params):
        self._id += 1
        payload = {"jsonrpc": "2.0", "id": self._id, "method": method, "params": params}
        try:
            resp = requests.post(self.url, json=payload, timeout=self.timeout)
            resp.raise_for_status()
        except requests.RequestException as e:
            raise RpcError(f"rpc {method} transport error: {e}") from e
        body = resp.json()
        if "error" in body and body["error"]:
            raise RpcError(f"rpc {method} error: {body['error']}")
        return body.get("result")

    def get_code(self, address, block="latest"):
        return self.call("eth_getCode", [address, block])

    def get_storage_at(self, address, slot, block="latest"):
        return self.call("eth_getStorageAt", [address, slot, block])

    def eth_call(self, to, data, block="latest"):
        return self.call("eth_call", [{"to": to, "data": data}, block])
