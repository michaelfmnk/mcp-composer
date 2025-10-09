from fastmcp.server.proxy import ProxyClient


class CustomProxyClient(ProxyClient):
    def __init__(self, *args, owner_email: str, **kwargs):
        self.owner_email = owner_email
        super().__init__(*args, **kwargs)
