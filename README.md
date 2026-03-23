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

## Updates (v1.1)

This version focuses on stabilizing and securing the server before adding advanced features.

### Fixes & Improvements

- Implemented safe path handling to prevent directory traversal (`../`) attacks
- Removed global state for folder rendering (preparing for future concurrency support)
- Added proper 404 handling for missing files
- Improved request handling with larger buffer size
- Added MIME type detection for correct file serving
  - Images now render correctly in browser
  - Supports multiple file types (png, jpg, txt, etc.)
- Improved error handling for file access and directory reading
- Cleaned routing logic for `/browse` and `/file`

### Current Capabilities

- HTTPS server using TLS (self-signed certificate)
- Recursive folder browsing
- Static file serving from vault directory
- Works across devices (laptop + mobile)
- Correct handling of binary and text files

### Known Limitations

- Markdown files are currently rendered as plain text
- Obsidian-specific syntax (`![[...]]`, `[[...]]`) is not yet supported
- No file editing or write functionality
- Single-threaded (no concurrent client handling yet)

### Next Steps

- Markdown rendering support
- Obsidian-style embed and link parsing
- Multi-threaded request handling
- JSON API for programmatic access

## Updates (v1.3)

This version marks a major transition from a read-only file server to a write-capable web editor.

### Remote Editing

The server now supports editing files directly from the browser using a simple HTML interface and HTTP POST requests.

### Features Added
- Added /save route for editing files
- Implemented HTML form-based editing interface with ``<textarea>``
- Added POST request handling for writing data to disk
- Enabled file modification over HTTPS from any device on the same network
- Supports appending content to existing files (initial editing model)

### Editing Flow
```Browse → Open File → Click "Write" → Edit → Save → File Updated```


### How It Works
-  GET `/save/<path>`
- Renders an editor view with the file content and a textarea
POST /save
- Receives form data (content, path) and writes it to disk
- Form submission uses application/x-www-form-urlencoded encoding
which is manually parsed from raw socket data

### Architectural Shift

This version transforms the system from:

Static Viewer → Interactive Editor

The server is no longer just serving files — it now modifies persistent state, making it a minimal web application.

### Current Limitations
- Editing is currently append-only (does not overwrite full file)
- No authentication (anyone on the network can edit files)
- No conflict handling or versioning
- No concurrency (single-threaded)
- No input validation beyond basic path safety

###  Next Steps
- Full file editing (overwrite instead of append)
- Pre-filled textarea with existing file content
- Redirect after save (improved UX)
- Basic authentication layer
- Improved UI/UX for mobile editing
- Better request parsing (handle large POST bodies)

### Project Evolution

This project has evolved from:

Low-level HTTPS server
→ File browser
→ Markdown renderer
→ Obsidian viewer
→ Web-based editor (current)

The long-term goal is to build a lightweight system similar to Obsidian Sync:

View notes on mobile
Edit notes remotely
Sync changes directly to local vault via HTTPS
No heavy frameworks or external dependencies
