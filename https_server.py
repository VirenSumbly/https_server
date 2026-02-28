"""
  server
"""

import socket
import ssl
import os
from urllib.parse import unquote

# Define socket host and port
SERVER_HOST = '0.0.0.0'
SERVER_PORT = 8443
VAULT_DIR = "C:/Users/Viren/ObsdianVaults/obsvault/obs.vault"

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain("cert.pem","key.pem")#public cert, private key


# Create socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((SERVER_HOST, SERVER_PORT))
server_socket.listen(2)#no. of clients 
print('Listening on port %s ...' % SERVER_PORT)

secure_server = context.wrap_socket(server_socket,server_side=True)
def render_folder(subpath=""):
    full_path = os.path.join(VAULT_DIR, subpath)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
    body {{
        font-family: sans-serif;
        font-size: 20px;
    }}
    a {{
        text-decoration: none;
    }}
    li {{
        margin: 8px 0;
    }}
    </style>
    </head>
    <body>
    <h1>{folder}</h1>
    <ul>
    """

    for item in os.listdir(full_path):
        item_path = os.path.join(full_path, item)
        new_path = os.path.join(subpath, item).replace("\\", "/")

        if os.path.isdir(item_path):
            html += f'<li><a href="/browse/{new_path}">{item}</a></li>'
        else:
            html += f'<li><a href="/file/{new_path}">{item}</a></li>'

    html += "</ul></body></html>"

    return html
while True:    
    # Wait for client connections
    #client_connection, client_address = server_socket.accept()
    
    try:
        client_connection, client_address = secure_server.accept()#tls handshake here
        print(f"client connected: {client_address}")
        
        # Get the client request
        request = client_connection.recv(1024)
        req_str = request.decode('utf-8',errors='ignore')
        print(req_str)

        #parse headers
        headers = req_str.split('\n')
        if len(headers) == 0 or len(headers[0].split()) < 2:
            client_connection.close()
            continue

        filename = headers[0].split()[1]
        
        if filename == "/" or filename == "/browse/" or filename == "/browse":
            folder = "Index"
            html = render_folder("")
            response = (
                b"HTTP/1.0 200 OK\r\n"
                b"Content-Type: text/html\r\n"
                b"\r\n" +
                html.encode()
            )
            client_connection.sendall(response)
            client_connection.close()
            continue

        
        if filename.startswith("/browse/"):
            folder = filename[len("/browse/"):]
            folder = unquote(folder)
            html = render_folder(folder)
            
            response=(
                b"HTTP/1.0 200 OK\r\n"
                b"Content-Type: text/html\r\n"
                b"\r\n" + 
                html.encode()
            )
            client_connection.sendall(response)
            client_connection.close()
            continue

        if filename.startswith("/file/"):
            file_path = filename[len("/file/"):]
            file_path = unquote(file_path)
            full_path = os.path.join(VAULT_DIR, file_path)

            with open(full_path, "rb") as f:
                content = f.read()

            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
            body {{
                font-family: sans-serif;
                font-size: 20px;
                white-space: pre-wrap;
            }}
            </style>
            </head>
            <body>
            {content.decode(errors="ignore")}
            </body>
            </html>
            """

            response = (
                b"HTTP/1.0 200 OK\r\n"
                b"Content-Type: text/html\r\n"
                b"\r\n" +
                html.encode()
            )

            client_connection.sendall(response)
            client_connection.close()
            continue
                    
        
        
        
        #Send HTTP response
        client_connection.sendall(response)
        client_connection.close()
    except ssl.SSLError as e:
        print("Handshake failed (normal for self-signed cert):", e)
        continue

    except Exception as e:
        print("Other error:", e)
        continue
# Close socket
secure_server.close()