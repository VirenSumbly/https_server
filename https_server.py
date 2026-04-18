"""
  server
"""

import socket
import ssl
import os
from urllib.parse import unquote,unquote_plus
import mimetypes
import markdown
import re
from html import escape 
from urllib.parse import parse_qs



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

    try:
        items = os.listdir(full_path)
    except Exception:
        return "<h1>Error reading directory</h1>"

    
    has_subdirs = any(os.path.isdir(os.path.join(full_path, i)) for i in items)

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
    .new-file-form {{
        margin-top: 30px;
        padding-top: 20px;
        border-top: 1px solid #ccc;
    }}
    .new-file-form input[type="text"] {{
        font-size: 18px;
        padding: 6px;
        width: 300px;
    }}
    .new-file-form button {{
        font-size: 18px;
        padding: 6px 14px;
        margin-left: 8px;
    }}
    </style>
    </head>
    <body>
    <h1>{title}</h1>
    <ul>
    """

    for item in items:
        item_path = os.path.join(full_path, item)
        new_path = os.path.join(subpath, item).replace("\\", "/")

        if os.path.isdir(item_path):
            html += f'<li><a href="/browse/{new_path}">{item}</a></li>'
        else:
            html += f'<li><a href="/file/{new_path}">{item}</a></li>'

    html += "</ul>"

    # for leaf  folders, show new file form
    if not has_subdirs:
        html += f"""
        <div class="new-file-form">
            <form method="POST" action="/newfile">
                <input type="text" name="filename" placeholder="new-note.md" required>
                <input type="hidden" name="folder" value="{subpath}">
                <button type="submit">+ New File</button>
            </form>
        </div>
        """

    html += "</body></html>"
    return html
#main loop
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
        
        method = headers[0].split()[0]
        filename = headers[0].split()[1]
        
        #Routes
        
        #/
        if method == "GET" and (filename == "/" or filename == "/browse/" or filename == "/browse"):
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
        elif method == "GET" and filename.startswith("/browse/"):
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
        elif method == "GET" and filename.startswith("/file/"):
            file_path = unquote(filename[len("/file/"):])
            full_path = safe_path(VAULT_DIR, file_path)
            print(file_path)
            print(full_path)

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
                #markdown handle
                if full_path.endswith(".md"):
                    current_dir = os.path.dirname(file_path)
                    md_text = content.decode(errors="ignore")
                    
                    md_text = parse_obsidian_embeds(md_text)
                    md_text = parse_obsidian_links(md_text,current_dir)
                    
                    
                    html_body = markdown.markdown(md_text)
                    
                    #html_body = markdown.markdown(content.decode(errors="ignore"))
                    # html_body = html_body.replace('src="', 'src="/file/')             
                    
                    # def Write():
                    #     print("hello")
                    #     #get the file, have an input box in the html at the end
                    #     # have an button that takes all the characters in the input box and does a post. 
                    #     # i think i have to first just break/ continue and give the filename
                    #     # saveObj = {
                    #     #     "html_Body" : html_body,
                            
                            
                    #     # }
                    #     full_path +="/save"
                    #     continue 
                    
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
                    <a href="/save/{file_path}">Edit</a>
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
                #mimetype code    
                else:
                                
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
            
                # /save
        #save
        elif method == "GET" and filename.startswith("/save/"):
            print("hello")

            file_path = filename[len("/save/"):]
            file_path = unquote(file_path)
            print("GET PATH:", repr(file_path))
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
                    md_text = parse_obsidian_links(md_text, current_dir)

                    html_body = markdown.markdown(md_text)

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
                    textarea {{
                        width: 100%;
                        height: 200px;
                        margin-top: 20px;
                    }}
                    </style>
                    <script>
                        txt = document.getElememtById("journal-box")
                    </script>
                    </head>
                    <body>
                    {html_body}
                    <form method="POST" action="/save">
                        <textarea name="content"></textarea>
                        <input type="hidden" name="path" value="{file_path}">
                        <button type="submit">Append</button>
                        <a href="/overwrite/{file_path}">Overwrite</a>
                    </form>
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
                      
        elif method == "POST" and filename == "/save":
            print("POST")
            #request = client_connection.recv(8192)
            
            headers_part, body = request.split(b"\r\n\r\n",1)
            
            body_str = body.decode()
            
            pairs = body_str.split("&")
            data = {}
            for pair in pairs:
                if "=" in pair:
                    key,value = pair.split("=",1)
                    data[key] = unquote_plus(value)
                
            content = data.get("content","").strip()
            
            path  = data.get("path","")
            print("POST PATH:", repr(path))
            
            absPath = safe_path(VAULT_DIR,path)
            
            if not absPath or not os.path.exists(absPath):
                response =(
                    b"HTTP/1.0 500 Internal Server Error\r\n"
                    b"Content-Type: text/html\r\n"
                    b"\r\n"
                    b"<h1>Error File Not Found</h1>"
                )
                client_connection.sendall(response)
                client_connection.close()
                continue
                
                
            content = content + "\n"
            
            with open(absPath,'a',encoding="utf-8") as myFile:
                myFile.write("\n"+content)
            
            response = (
                b"HTTP/1.0 200 OK\r\n"
                b"Content-Type: text/html\r\n"
                b"\r\n"
                b"<h1>Saved</h1>"
            )
            
            client_connection.sendall(response)
            client_connection.close()
            continue
        elif method == "GET" and filename.startswith("/overwrite/"):
            print("HIT OVERWRITE GET")

            file_path = filename[len("/overwrite/"):]
            file_path = unquote(file_path)

            full_path = safe_path(VAULT_DIR, file_path)

            if not full_path or not os.path.exists(full_path):
                response = (
                    b"HTTP/1.0 404 Not Found\r\n"
                    b"Content-Type: text/html\r\n\r\n"
                    b"<h1>404 Not Found</h1>"
                )
                client_connection.sendall(response)
                client_connection.close()
                continue

            import html

            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()

            safe_content = html.escape(content)

            html_page = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                body {{
                    margin: 0;
                }}
                button {{
                    display: block;
                    margin: 10px auto;
                    padding: 8px 20px;
                    font-size: 16px;
                }}
                textarea {{
                display: block;
                width: 80%;
                height: 65vh;
                box-sizing: border-box;
                padding: 15px;
                font-size: 16px;
                font-family: monospace;
                margin: 0 auto;
            }}
                </style>
            </head>
            <body>
                <h2>Editing: {file_path}</h2>

                <form method="POST" action="/overwrite">
                    <textarea name="content">{safe_content}</textarea>
                    <input type="hidden" name="path" value="{file_path}">
                    <br>
                    <button type="submit">Save</button>
                </form>
            </body>
            </html>
            """

            response = (
                b"HTTP/1.0 200 OK\r\n"
                b"Content-Type: text/html\r\n\r\n" +
                html_page.encode()
            )

            client_connection.sendall(response)
            client_connection.close()
            continue
        

        elif method == "POST" and filename == "/overwrite":
            parts = request.split(b"\r\n\r\n", 1)

            if len(parts) < 2:
                client_connection.close()
                continue

            headers_part = parts[0].decode(errors='ignore') 
            body = parts[1]                                   

            content_length = 0
            for line in headers_part.split('\r\n'):
                if line.lower().startswith("content-length:"):
                    content_length = int(line.split(":", 1)[1].strip())  
                    break

            while len(body) < content_length:
                chunk = client_connection.recv(8192)
                if not chunk:
                    break
                body += chunk

            data = parse_qs(body.decode('utf-8', errors='ignore'))

            content = data.get("content", [""])[0] 
            path = data.get("path", [""])[0]        

            if not path:
                print("Error: No path received in POST")
                client_connection.close()
                continue

            absPath = safe_path(VAULT_DIR, path)
            print("Targeting file:", absPath)

            if absPath and os.path.exists(absPath) and os.path.isfile(absPath):
                with open(absPath, 'w', encoding="utf-8") as myFile:
                    myFile.write(content)

                response = (
                    b"HTTP/1.0 200 OK\r\n"
                    b"Content-Type: text/html\r\n\r\n"
                    b"<h1>Saved</h1><a href='/file/" + path.encode() + b"'>Back</a>"
                )
            else:
                print("Permission Error Prevention: Path is directory or invalid.")
                response = b"HTTP/1.0 403 Forbidden\r\n\r\n<h1>Cannot overwrite a directory</h1>"

            client_connection.sendall(response)
            client_connection.close()
            continue
        
        elif method == "POST" and filename == "/newfile":
            parts = request.split(b"\r\n\r\n", 1)
            if len(parts) < 2:
                client_connection.close()
                continue

            headers_part = parts[0].decode(errors='ignore')
            body = parts[1]

            content_length = 0
            for line in headers_part.split('\r\n'):
                if line.lower().startswith("content-length:"):
                    content_length = int(line.split(":", 1)[1].strip())
                    break

            while len(body) < content_length:
                chunk = client_connection.recv(8192)
                if not chunk:
                    break
                body += chunk

            data = parse_qs(body.decode('utf-8', errors='ignore'))
            filename_new = data.get("filename", [""])[0].strip()
            folder = data.get("folder", [""])[0].strip()

            # Add .md extension if user forgot it
            if filename_new and not os.path.splitext(filename_new)[1]:
                filename_new += ".md"

            if not filename_new:
                response = (
                    b"HTTP/1.0 400 Bad Request\r\n"
                    b"Content-Type: text/html\r\n\r\n"
                    b"<h1>No filename provided</h1>"
                )
                client_connection.sendall(response)
                client_connection.close()
                continue

            new_rel_path = os.path.join(folder, filename_new).replace("\\", "/")
            new_abs_path = safe_path(VAULT_DIR, new_rel_path)

            if not new_abs_path:
                response = (
                    b"HTTP/1.0 403 Forbidden\r\n"
                    b"Content-Type: text/html\r\n\r\n"
                    b"<h1>Invalid path</h1>"
                )
                client_connection.sendall(response)
                client_connection.close()
                continue

            if os.path.exists(new_abs_path):
                response = (
                    b"HTTP/1.0 409 Conflict\r\n"
                    b"Content-Type: text/html\r\n\r\n"
                    b"<h1>File already exists</h1>"
                )
                client_connection.sendall(response)
                client_connection.close()
                continue

            # Create the empty file
            with open(new_abs_path, 'w', encoding='utf-8') as f:
                f.write("")

            # Redirect to the overwrite/edit page so user can start writing
            redirect_path = new_rel_path.replace(" ", "%20")
            response = (
                b"HTTP/1.0 302 Found\r\n"
                b"Location: /overwrite/" + redirect_path.encode() + b"\r\n"
                b"\r\n"
            )
            client_connection.sendall(response)
            client_connection.close()
            continue
                
        
        
            
        # 🔹 Unknown route
        else:
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
