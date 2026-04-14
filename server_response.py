from datetime import datetime, timezone

class ServerResponse:
    def __init__(self):
        self.status = "200 OK"
        self.headers = {
            "Date": 0,
            "Connection": "close",
            "Content-Length": 0
        }
        self.body = b""
        self.is_error = False
        self.log_headers = ""
        self.log = ""

    def build_response(self):
        self.update_response_date()
        self.update_response_length()

        response = f"HTTP/1.1 {self.status}\r\n"
        for key, value in self.headers.items():
            response += f"{key}: {value}\r\n"
        response += f"\r\n"

        return response.encode() + self.body

    def update_response_date(self):
        self.headers["Date"] = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")

    def update_response_length(self):
        self.headers["Content-Length"] = len(self.body)

    def create_log(self, client_address):
        if self.is_error:
            self.log = f"client {client_address} has recieved an error: {self.status}"
        else:
            self.log = f"client {client_address} has connected with headers: {self.log_headers}, and received status {self.status}"
