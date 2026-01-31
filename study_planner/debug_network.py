import os
import socket
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

url = os.environ.get("SUPABASE_URL")
print(f"Loaded URL: '{url}'")
print(f"Repr URL: {repr(url)}")

if url:
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        print(f"Hostname: '{hostname}'")
        
        print("Attempting DNS resolution...")
        info = socket.getaddrinfo(hostname, 443)
        print("DNS Resolution success:", info)
    except Exception as e:
        print(f"DNS Resolution failed: {e}")
else:
    print("URL not found in environment")
