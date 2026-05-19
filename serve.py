#!/usr/bin/env python3
"""
BattleTech HQ — Local Development Server
=========================================
Serves the site locally so you can test before pushing live.

Usage:
    python serve.py                  # Serves on http://localhost:8000
    python serve.py --port 3000      # Custom port
    python serve.py --host 0.0.0.0   # Accessible on local network (other devices)

Requirements: Python 3.6+ (no extra packages needed)
"""

import http.server
import socketserver
import os
import sys
import argparse
import webbrowser
import threading
import time
from pathlib import Path

# ── Colour output ─────────────────────────────────────────────────────────────
class C:
    ORANGE = '\033[38;5;208m'
    CYAN   = '\033[96m'
    GREEN  = '\033[92m'
    YELLOW = '\033[93m'
    RED    = '\033[91m'
    GREY   = '\033[90m'
    BOLD   = '\033[1m'
    RESET  = '\033[0m'

# ── Custom handler with logging ───────────────────────────────────────────────
class BattleTechHandler(http.server.SimpleHTTPRequestHandler):

    # MIME types for all file types the site uses
    MIME_TYPES = {
        '.html': 'text/html; charset=utf-8',
        '.css':  'text/css; charset=utf-8',
        '.js':   'application/javascript; charset=utf-8',
        '.json': 'application/json; charset=utf-8',
        '.jpg':  'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png':  'image/png',
        '.gif':  'image/gif',
        '.webp': 'image/webp',
        '.svg':  'image/svg+xml',
        '.ico':  'image/x-icon',
        '.woff': 'font/woff',
        '.woff2':'font/woff2',
        '.ttf':  'font/ttf',
        '.mul':  'application/xml',
        '.xml':  'application/xml',
        '.pdf':  'application/pdf',
        '.zip':  'application/zip',
    }

    def end_headers(self):
        # Allow local file access (fixes CORS issues when testing locally)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def guess_type(self, path):
        ext = Path(path).suffix.lower()
        return self.MIME_TYPES.get(ext, 'application/octet-stream')

    def log_message(self, format, *args):
        code = args[1] if len(args) > 1 else '???'
        path = args[0].split()[1] if args else '/'

        # Colour code by response type
        if str(code).startswith('2'):
            colour = C.GREEN
        elif str(code).startswith('3'):
            colour = C.CYAN
        elif str(code).startswith('4'):
            colour = C.YELLOW if code == '404' else C.RED
        else:
            colour = C.GREY

        # Shorten long paths for readability
        display_path = path if len(path) < 60 else '...' + path[-57:]

        print(f"{C.GREY}[{self.log_date_time_string()}]{C.RESET} "
              f"{colour}{code}{C.RESET} "
              f"{display_path}")

    def log_error(self, format, *args):
        # Suppress the default error spam for 404s
        pass

# ── Server setup ──────────────────────────────────────────────────────────────
def find_site_root():
    """
    Auto-detect the site root directory.
    Looks for index.html in current dir or common subdirs.
    """
    candidates = [
        Path('.'),
        Path('site_fixed'),
        Path('site'),
        Path('dist'),
        Path('public'),
    ]
    for candidate in candidates:
        if (candidate / 'index.html').exists():
            return candidate.resolve()
    return Path('.').resolve()


def open_browser(url, delay=1.0):
    """Open browser after a short delay to let the server start."""
    def _open():
        time.sleep(delay)
        webbrowser.open(url)
    threading.Thread(target=_open, daemon=True).start()


def print_banner(host, port, site_root):
    print()
    print(f"{C.ORANGE}{C.BOLD}{'='*55}{C.RESET}")
    print(f"{C.ORANGE}{C.BOLD}  ⚙  BATTLETECH HQ — LOCAL SERVER{C.RESET}")
    print(f"{C.ORANGE}{C.BOLD}{'='*55}{C.RESET}")
    print(f"  {C.CYAN}Site root:{C.RESET}  {site_root}")
    print(f"  {C.CYAN}Local:{C.RESET}      {C.GREEN}http://localhost:{port}{C.RESET}")
    if host == '0.0.0.0':
        import socket
        try:
            ip = socket.gethostbyname(socket.gethostname())
            print(f"  {C.CYAN}Network:{C.RESET}    {C.GREEN}http://{ip}:{port}{C.RESET}  ← other devices on your network")
        except:
            pass
    print()
    print(f"  {C.GREY}Key pages:{C.RESET}")
    print(f"  {C.GREY}  Homepage:      http://localhost:{port}/{C.RESET}")
    print(f"  {C.GREY}  Lance Builder: http://localhost:{port}/lance-builder.html{C.RESET}")
    print(f"  {C.GREY}  About:         http://localhost:{port}/about.html{C.RESET}")
    print()
    print(f"  {C.YELLOW}Press Ctrl+C to stop the server{C.RESET}")
    print(f"{C.ORANGE}{'='*55}{C.RESET}")
    print()


def run(host='localhost', port=8000, no_browser=False):
    site_root = find_site_root()
    os.chdir(site_root)

    # Allow port reuse so you can restart quickly
    socketserver.TCPServer.allow_reuse_address = True

    try:
        with socketserver.TCPServer((host, port), BattleTechHandler) as httpd:
            url = f"http://localhost:{port}"
            print_banner(host, port, site_root)

            if not no_browser:
                open_browser(url)
                print(f"  {C.GREY}Opening browser...{C.RESET}\n")

            print(f"  {C.GREY}Requests:{C.RESET}")
            httpd.serve_forever()

    except OSError as e:
        if 'Address already in use' in str(e):
            print(f"\n{C.RED}Port {port} is already in use.{C.RESET}")
            print(f"Try a different port:  {C.CYAN}python serve.py --port {port + 1}{C.RESET}\n")
        else:
            raise
    except KeyboardInterrupt:
        print(f"\n\n{C.ORANGE}Server stopped. For the Star League.{C.RESET}\n")


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='BattleTech HQ local development server',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python serve.py                    Start on http://localhost:8000
  python serve.py --port 3000        Use port 3000
  python serve.py --host 0.0.0.0     Accessible to other devices on your network
  python serve.py --no-browser       Don't auto-open the browser
        """
    )
    parser.add_argument('--host',       default='localhost', help='Host to bind to (default: localhost)')
    parser.add_argument('--port', '-p', default=8000, type=int, help='Port to serve on (default: 8000)')
    parser.add_argument('--no-browser', action='store_true', help="Don't automatically open the browser")
    args = parser.parse_args()

    run(host=args.host, port=args.port, no_browser=args.no_browser)
