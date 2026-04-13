from datetime import datetime, timezone

class ServerResponse:
    def __init__(self):
        self.status = "200 OK"
        self.headers = {
            "Date": 0,
            "Connection": "close",
            "Content-Length": 0
        }
        self.body = ""

    def build_response(self):
        self.update_response_date()
        self.update_response_length()

        response = f"HTTP/1.1 {self.status}\r\n"
        for key, value in self.headers.items():
            response += f"{key}: {value}\r\n"
        response += f"\r\n{self.body}"
        return response

    def update_response_date(self):
        self.headers["Date"] = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")

    def update_response_length(self):
        self.headers["Content-Length"] = len(self.body)
