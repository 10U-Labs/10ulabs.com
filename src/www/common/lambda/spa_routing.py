"""Lambda@Edge handler for SPA routing."""


def handler(event, _context):
    """Handle viewer-request events for SPA routing.

    This function runs at CloudFront edge locations and handles:
    1. Apex to www redirect (e.g., example.com -> www.example.com)
    2. SPA routing (paths without extensions get index.html)

    Args:
        event: CloudFront viewer-request event
        _context: Lambda context (unused)

    Returns:
        Modified request or redirect response
    """
    request = event["Records"][0]["cf"]["request"]
    host = request["headers"].get("host", [{}])[0].get("value", "")
    uri = request["uri"]

    # Apex to www redirect (if host doesn't start with "www.")
    if not host.startswith("www."):
        www_host = "www." + host
        return {
            "status": "301",
            "statusDescription": "Moved Permanently",
            "headers": {
                "location": [{"key": "Location", "value": f"https://{www_host}{uri}"}]
            }
        }

    # Rewrite /assets/* to /home/assets/* for home page static files
    if uri.startswith("/assets/"):
        request["uri"] = "/home" + uri
        return request

    # Serve files with extensions as-is
    if "." in uri:
        return request

    # Root path -> /home/index.html
    if uri in ("/", ""):
        request["uri"] = "/home/index.html"
        return request

    # Ensure trailing slash, then append index.html
    if not uri.endswith("/"):
        uri = uri + "/"
    request["uri"] = uri + "index.html"
    return request
