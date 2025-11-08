from typing import Optional

SUCCESS: str
FAILED: str

def send(
    event: dict,
    context: object,
    responseStatus: str,
    responseData: dict,
    physicalResourceId: Optional[str] = None,
    noEcho: bool = False,
    reason: Optional[str] = None
) -> None: ...
