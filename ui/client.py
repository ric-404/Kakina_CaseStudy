"""HTTP client: CLI menus communicate with the local FastAPI REST API."""
import httpx

BASE_URL = 'http://127.0.0.1:8765'


class ApiError(Exception):
    pass


class ApiClient:
    def __init__(self):
        self.http = httpx.Client(base_url=BASE_URL, timeout=12)

    def call(self, method, path, payload=None, params=None):
        try:
            response = self.http.request(method, path, json=payload, params=params)
        except httpx.RequestError as exc:
            raise ApiError('Cannot connect to local FastAPI server.') from exc
        if response.is_error:
            try:
                detail = response.json().get('detail', response.text)
            except ValueError:
                detail = response.text
            if isinstance(detail, list):
                detail = '; '.join(x.get('msg', 'Invalid input') for x in detail)
            raise ApiError(f'{detail} (HTTP {response.status_code})')
        return response.json() if response.content else None

    def close(self):
        self.http.close()
