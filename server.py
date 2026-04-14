import os
import random
import socket
import string
from datetime import datetime, timezone
import mysql.connector
from server_response import ServerResponse


HOST = "0.0.0.0"
PORT = 80
BUFFER = 4096
ABSOLUTE_SITE_DIRECTORY_PATH = r"C:\Users\lb06ng01\Documents\hachshara\WEB\SERVER SIDE\site-files"


def insert_log_to_db(log):
    mysql_db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Lit1337!",
        database="server-side-schema")

    mysql_cursor = mysql_db.cursor()

    mysql_cursor.execute(f"insert into loger_table (log_data) values ('{log}');")
    mysql_db.commit()

    mysql_db.close()


def create_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"listening on {HOST}:{PORT}")

    while True:
        client_socket, client_address = server.accept()
        with client_socket:
            print(f"Client {client_address} connected")
            # threading.Thread(target=handle_client, args=(client_socket, client_address)).start()
            handle_client(client_socket, client_address)


def handle_client(client_socket, client_address):
    is_data_finished = False
    request_data = ""
    while not is_data_finished:
        request_data += client_socket.recv(BUFFER).decode()
        print(f"Received: \n{request_data}")
        if "\r\n\r\n" in request_data:
            is_data_finished = True

    print(f"Received: \n{request_data}")

    server_response = parse_handle_request(request_data, client_address)
    response = server_response.build_response()
    client_socket.send(response)
    print(f"Sent: \n{response}")

    try:
        while "'" in log or '"' in log:
            log = log.replace("'", "")
            log = log.replace('"', "")

        insert_log_to_db(log)

    except Exception:
        print("loger has failed :(")

    client_socket.close()


def parse_handle_request(request_data, client_address):
    server_response = ServerResponse()

    is_not_modified = False
    is_unmodified = False

    try:
        try:
            start_line, headers_with_body = request_data.split("\r\n", 1)

            request_method, request_path, request_protocol = start_line.split(" ")
            request_method = request_method.upper().strip()
            request_path = request_path.strip()
            request_protocol = request_protocol.upper().strip()
        except Exception:
            server_response.status = "400 Bad Request"
            return server_response

        if request_protocol != "HTTP/1.1":
            server_response.status = "505 HTTP Version Not Supported"
            return server_response

        if request_method != "GET":
            server_response.status = "405 Method Not Allowed"
            return server_response

        # check if path exists
        if request_path == "/":
            request_path = "index.html"

        absolute_request_path = ABSOLUTE_SITE_DIRECTORY_PATH + "\\" + request_path

        if not os.path.isfile(absolute_request_path) or os.path.dirname(absolute_request_path) != ABSOLUTE_SITE_DIRECTORY_PATH:
            server_response.status = "404 Not Found"
            return server_response

        # check headers and build response
        file_content = open(absolute_request_path, "rb").read()
        response_body = file_content

        try:
            file_mtime = os.path.getmtime(absolute_request_path)
            file_last_modified = datetime.fromtimestamp(file_mtime, timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
        except Exception:
            file_last_modified = ""

        try:
            headers, body = headers_with_body.split("\r\n\r\n", 1)
        except Exception:
            server_response.status = "400 Bad Request"
            return server_response

        headers = headers.split("\r\n")
        is_host_exist = False
        for header in headers:
            try:
                header_name, header_value = header.split(":", 1)
            except Exception:
                server_response.status = "400 Bad Request"
                return server_response

            header_name = header_name.upper()
            header_value = header_value.strip()

            if header_name in ["DATE", "USER-AGENT"]:
                if header_name == "DATE":
                    if not is_valid_http_date(header_value):
                        continue
                server_response.log_headers += header_name + ": " + header_value + "\n"

            # if unmodified is checked before is modified
            if header_name == "IF-UNMODIFIED-SINCE":
                is_unmodified = True
                # A recipient MUST ignore the If-Modified-Since header field if the received field value is not a valid HTTP-date
                if not is_valid_http_date(header_value) or not file_last_modified:
                    continue

                last_modified = datetime.strptime(file_last_modified, "%a, %d %b %Y %H:%M:%S GMT")
                http_if_modified_since = datetime.strptime(header_value, "%a, %d %b %Y %H:%M:%S GMT")

                if http_if_modified_since < last_modified:
                    server_response.headers["Last-Modified"] = file_last_modified
                    server_response.status = "412 Precondition Failed"
                    return server_response
                else:
                    server_response.status = "200 OK"
                    continue

            if header_name == "IF-MODIFIED-SINCE" and not is_unmodified:
                # A recipient MUST ignore the If-Modified-Since header field if the received field value is not a valid HTTP-date
                if not is_valid_http_date(header_value) or not file_last_modified:
                    continue

                last_modified = datetime.strptime(file_last_modified, "%a, %d %b %Y %H:%M:%S GMT")
                http_if_modified_since = datetime.strptime(header_value, "%a, %d %b %Y %H:%M:%S GMT")

                if http_if_modified_since < last_modified:
                    server_response.status = "200 OK"
                    continue
                else:
                    server_response.status = "304 Not Modified"
                    is_not_modified = True
                    continue

            if header_name == "RANGE" and not is_not_modified:
                try:
                    range_units, range_value = header_value.split("=", 1)
                    range_units = range_units.strip()
                    range_value = range_value.strip()

                    ranges = range_value.split(",")
                    if len(ranges) == 1:
                        # If a single part is being transferred,
                        # the server generating the 206 response MUST generate a Content-Range header field,
                        # describing what range of the selected representation is enclosed, and a payload consisting of the range.
                        range_content, status = get_range_content(ranges[0], range_units, file_content)
                        if not status and not range_content: # ignore header
                            continue

                        if status: # error
                            server_response.status = status
                            response = server_response.build_response()
                            return response, f"client {client_address} has recieved an error: {response}"

                        server_response.headers["Content-Range"] = f"{ranges[0]}/{len(file_content)}"
                        server_response.status = "206 Partial Content"
                        response_body = range_content

                    else:
                        # If multiple parts are being transferred,
                        # the server generating the 206 response MUST generate a "multipart/byteranges" payload
                        string_separator = get_string_separator(file_content)
                        response_body = ""
                        for current_range in ranges:
                            range_content, status = get_range_content(current_range, range_units, file_content)
                            if not status and not range_content: # ignore header
                                continue
                            if status: # error
                                server_response.status = status
                                return server_response

                            response_body += f"--{string_separator}\r\nContent-Range: bytes {current_range}/{len(file_content)}\r\n\r\n{range_content}\r\n"

                        response_body += f"--{string_separator}--\r\n"
                        server_response.headers["Content-Type"] = f"multipart/byteranges; boundary={string_separator}"
                        server_response.status = "206 Partial Content"

                    server_response.log_headers += header_name + ": " + header_value + "\n"

                except Exception:
                    server_response.status = "400 Bad Request"
                    return server_response

            if header_name == "HOST":
                is_host_exist = True

        if not is_host_exist:
            server_response.status = "400 Bad Request"
            return server_response

        if file_last_modified:
            server_response.headers["Last-Modified"] = file_last_modified

        server_response.body = response_body
        # success
        if is_not_modified and not is_unmodified:
            server_response.body = ""

        return server_response

    except Exception:
        server_response.status = "500 Internal Server Error"
        return server_response


def is_valid_http_date(date):
    try:
        datetime.strptime(date, "%a, %d %b %Y %H:%M:%S GMT")
        return True
    except Exception:
        return False


def get_range_content(given_range, range_units, file_content):
    try:
        if range_units.upper() != "BYTES":
            # An origin server MUST ignore a Range header field that contains a range unit it does not understand.
            return "", ""
        try:
            # A server that supports range requests MAY ignore or reject a Range header field that contains an invalid ranges-specifier
            start_range, end_range = given_range.split("-", 1)
        except Exception:
            return "", ""

        start_range = start_range.strip()
        end_range = end_range.strip()

        if start_range == "" and end_range.isdigit():
            end_range = int(end_range)
            if end_range >= len(file_content):
                return "", "416 Range Not Satisfiable"
            return file_content[-end_range:]+ "\r\n", ""

        elif end_range == "" and start_range.isdigit():
            start_range = int(start_range)
            if start_range >= len(file_content):
                return "", "416 Range Not Satisfiable"
            return file_content[start_range:]+ "\r\n", ""

        elif start_range.isdigit() and end_range.isdigit():
            start_range = int(start_range)
            end_range = int(end_range)
            if start_range > end_range or end_range + 1 >= len(file_content):
                return "", "416 Range Not Satisfiable"
            return file_content[start_range:end_range + 1] + "\r\n", ""

        # A server that supports range requests MAY ignore or reject a Range header field that contains an invalid ranges-specifier
        return "", ""

    except Exception:
        return "", "500 Internal Server Error"


def get_string_separator(file_content):
    string_separator = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    while string_separator in file_content:
        string_separator = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

    return string_separator


if __name__ == '__main__':
    create_server()
