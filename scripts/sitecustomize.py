"""
Python startup customization for Claude SEO scripts.

When available, prefer the OS-native trust store so HTTPS requests work
reliably on platforms where OpenSSL CA bundles are incomplete or divergent
from the system certificate store.
"""

try:
    import truststore
except Exception:
    truststore = None

if truststore is not None:
    try:
        truststore.inject_into_ssl()
    except Exception:
        # If injection fails, fall back to the default SSL behavior.
        pass
