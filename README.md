# HTTPS Server from Scratch in Python

This project implements a minimal HTTPS file server from scratch using Python's `socket` and `ssl` modules, without relying on web frameworks such as Flask, Django, or Node.js.

The goal of this project is to understand how secure web servers work at a low level by manually building the network stack integration between TCP, TLS, and HTTP.

The server supports:

- TCP socket creation and connection handling
- TLS encryption using a self-signed certificate
- HTTPS communication with browsers and LAN devices
- Basic HTTP/1.0 request parsing
- Static file serving from a local directory (`htdocs/`)

This project demonstrates how HTTPS is fundamentally implemented as HTTP over a TLS-encrypted transport layer.

It serves as a foundation for building more advanced systems such as secure APIs, file synchronization services, or lightweight web applications without relying on external frameworks.

---

## Features

- HTTPS support using TLS (self-signed certificate)
- HTTP/1.0 request handling
- Static file serving from `htdocs/`
- Works with modern browsers and mobile devices
- No external dependencies (standard library only)

---

## Purpose

This project was built to understand how HTTPS servers work internally, including TLS handshakes, certificate-based encryption, and HTTP communication over secure sockets.

It avoids using frameworks to expose the underlying mechanics of secure network communication.

---

## Note

This server requires a self-signed TLS certificate.

Generate one using OpenSSL:

```bash
openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
-keyout key.pem -out cert.pem \
-subj "/CN=localhost"
```
This creates 
```
cert.pem   # public certificate  
key.pem    # private key
```
Place them in the root of the project

After generating the cert.pem and key.pem, run the server

## Running the Server
Start the server
```bash
python3 http_server.py
```
Then open your browser and navigate to

```Code
https://localhost:8443
```
If accessing from some other device on the same network like phone, 
```Code
https://<your-local-ip>:8443
```
Example:
```Code
https://192.168.0.5:8443
```
You may need to accept a security warning since the certificate is self-signed.