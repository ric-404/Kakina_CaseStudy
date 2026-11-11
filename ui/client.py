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
                messages = []
                for item in detail:
                    messages.append(item.get('msg', 'Invalid input'))
                detail = '; '.join(messages)

            raise ApiError(f'{detail} (HTTP {response.status_code})')

        if response.content:
            return response.json()
        return None

    def close(self):
        self.http.close()
