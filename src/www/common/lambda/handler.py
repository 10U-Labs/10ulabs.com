from typing import Any, Dict


def lambda_handler(event: Dict[str, Any], _context: Any) -> Dict[str, Any]:
    request = event["Records"][0]["cf"]["request"]
    host = request["headers"].get("host", [{}])[0].get("value", "")
    uri = request["uri"]

    if not host.startswith("www."):
        www_host = "www." + host
        return {
            "status": "301",
            "statusDescription": "Moved Permanently",
            "headers": {
                "location": [{"key": "Location", "value": f"https://{www_host}{uri}"}]
            }
        }

    if uri.startswith("/assets/"):
        request["uri"] = "/home" + uri
        return request

    if "." in uri:
        return request

    if uri in ("/", ""):
        request["uri"] = "/home/index.html"
        return request

    if not uri.endswith("/"):
        return {
            "status": "301",
            "statusDescription": "Moved Permanently",
            "headers": {
                "location": [{"key": "Location", "value": f"https://{host}{uri}/"}]
            }
        }

    request["uri"] = uri + "index.html"
    return request
