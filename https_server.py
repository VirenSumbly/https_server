"""
  server
"""

import socket
import ssl

# Define socket host and port
SERVER_HOST = '0.0.0.0'
SERVER_PORT = 8443

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain("cert.pem","key.pem")#public cert, private key


# Create socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((SERVER_HOST, SERVER_PORT))
server_socket.listen(2)#no. of clients 
print('Listening on port %s ...' % SERVER_PORT)

secure_server = context.wrap_socket(server_socket,server_side=True)
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
        filename = headers[0].split()[1]
        
        
        #content from htdocs
        if filename =="/":
            filename = '/index.html'
        
        try:
            with open('htdocs' + filename,'rb') as fin:
                content = fin.read()
             
        
            response = (
                b'HTTP/1.0 200 OK\r\n'
                b'Content-Type: text/html\r\n'
                b'\r\n' + content
            )
        except FileNotFoundError:
            response = (
                b'HTTP/1.0 404 NOT FOUND\r\n'
                b'Content-Type: text/html\r\n'
                b'\r\n'
                b'<h1>404 Not Found</h1>'
            )
            
        # Send HTTP response
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