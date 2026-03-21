"""
  server
"""

import socket
import ssl
import os
from urllib.parse import unquote
import mimetypes
import markdown
import re

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
def safe_path(base, user_path):
    full_path = os.path.normpath(os.path.join(base, user_path))

    base_abs = os.path.abspath(base)
    full_abs = os.path.abspath(full_path)

    if not full_abs.startswith(base_abs):
        return None

    return full_abs

def resolve_link(filename,current_dir):
    candidate = os.path.join(current_dir,filename)
    candidate_md = candidate + ".md"
    full_path = os.path.join(VAULT_DIR,candidate_md)
    

    
    if os.path.exists(full_path):
        return candidate_md.replace("\\","/")
    
    #fallback
    for root,dirs,files in os.walk(VAULT_DIR):
        for f in files:
            if f == filename or f.startswith(filename + ".md"):
                rel_path = os.path.relpath(os.path.join(root,filename),VAULT_DIR)
                return rel_path.replace("\\","/")
    
    return None


def parse_obsidian_embeds(md_text):
    def repl(match):
        filename = match.group(1)

        # 👇 only treat images
        if filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
            path = f"Assets Tags Templates/Assets/{filename}"
            return f'<img src="/file/{path}">'

        # 👇 if not image, leave unchanged
        return match.group(0)

    return re.sub(r'!\[\[([^\]]+)\]\]', repl, md_text)

def parse_obsidian_links(md_text,current_dir):
    def repl(match):
        filename = match.group(1)

        # path = filename  # keep simple for now
        # print(path)
        path = resolve_link(filename, current_dir)
        
        if path:
            return f'<a href="/file/{path}">{filename}</a>'
        else:
            return filename

    return re.sub(r'(?<!\!)\[\[([^\]]+)\]\]', repl, md_text)



def render_folder(subpath=""):
    full_path = safe_path(VAULT_DIR, subpath)

    if not full_path or not os.path.exists(full_path):
        return "<h1>Access Denied</h1>"

    title = subpath if subpath else "Index"
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
    <h1>{title}</h1>
    <ul>
    """
    try:
        for item in os.listdir(full_path):
            item_path = os.path.join(full_path, item)
            new_path = os.path.join(subpath, item).replace("\\", "/")

            if os.path.isdir(item_path):
                html += f'<li><a href="/browse/{new_path}">{item}</a></li>'
            else:
                html += f'<li><a href="/file/{new_path}">{item}</a></li>'
    except Exception:
        return "<h1>Error reading directory</h1>"
    html += "</ul></body></html>"

    return html
while True:    
    # Wait for client connections
    #client_connection, client_address = server_socket.accept()
    
    try:
        client_connection, client_address = secure_server.accept()#tls handshake here
        print(f"client connected: {client_address}")
        
        # Get the client request
        request = client_connection.recv(8192)
        req_str = request.decode('utf-8',errors='ignore')
        print(req_str)

        #parse headers
        headers = req_str.split('\n')
        if len(headers) == 0 or len(headers[0].split()) < 2:
            client_connection.close()
            continue

        filename = headers[0].split()[1]
        #/
        if filename == "/" or filename == "/browse/" or filename == "/browse":
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

        
        #browse
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
        
        
        #files
        if filename.startswith("/file/"):
            file_path = unquote(filename[len("/file/"):])
            full_path = safe_path(VAULT_DIR, file_path)

            if not full_path or not os.path.exists(full_path):
                response = (
                    b"HTTP/1.0 404 Not Found\r\n"
                    b"Content-Type: text/html\r\n"
                    b"\r\n"
                    b"<h1>404 Not Found</h1>"
                )
                client_connection.sendall(response)
                client_connection.close()
                continue

            try:
                with open(full_path, "rb") as f:
                    content = f.read()
                if full_path.endswith(".md"):
                    current_dir = os.path.dirname(file_path)
                    md_text = content.decode(errors="ignore")
                    
                    md_text = parse_obsidian_embeds(md_text)
                    md_text = parse_obsidian_links(md_text,current_dir)
                    
                    
                    html_body = markdown.markdown(md_text)
                    
                    #html_body = markdown.markdown(content.decode(errors="ignore"))
                    # html_body = html_body.replace('src="', 'src="/file/')
                    
                    
                    
                    


                                        
                    
                    
                    
                    
                    
                    
                    
                    
                    html = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <style>
                    body {{
                        font-family: sans-serif;
                        max-width: 800px;
                        margin: auto;
                        padding: 20px;
                        line-height: 1.6;
                    }}
                    img {{
                        max-width: 100%;
                    }}
                    </style>
                    </head>
                    <body>
                    {html_body}
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
            except Exception:
                response = (
                    b"HTTP/1.0 500 Internal Server Error\r\n"
                    b"Content-Type: text/html\r\n"
                    b"\r\n"
                    b"<h1>Error reading file</h1>"
                )
                client_connection.sendall(response)
                client_connection.close()
                continue

            # MIME type detection
            mime_type, _ = mimetypes.guess_type(full_path)
            if mime_type is None:
                mime_type = "application/octet-stream"

            response = (
                b"HTTP/1.0 200 OK\r\n" +
                f"Content-Type: {mime_type}\r\n".encode() +
                b"\r\n" +
                content
            )

            client_connection.sendall(response)
            client_connection.close()
            continue

        # 🔹 Unknown route
        response = (
            b"HTTP/1.0 404 Not Found\r\n"
            b"Content-Type: text/html\r\n"
            b"\r\n"
            b"<h1>Route Not Found</h1>"
        )
        client_connection.sendall(response)
        client_connection.close()

    except ssl.SSLError as e:
        print("Handshake failed:", e)
        continue

    except Exception as e:
        print("Other error:", e)
        continue


secure_server.close()
