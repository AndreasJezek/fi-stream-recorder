from playwright.sync_api import Route

class StreamRecorder():
    def __init__(self):
        self.m3u8_url: str | None = None

    def handle_route(self, route: Route):
        if 'm3u8' in route.request.url:
            self.m3u8_url = route.request.url
        route.continue_()