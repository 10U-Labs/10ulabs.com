"""CloudFormation custom resource response stub for testing"""
SUCCESS = "SUCCESS"
FAILED = "FAILED"

def send(event, context, responseStatus, responseData, physicalResourceId=None, noEcho=False, reason=None):
    """Stub - does nothing, just prevents ImportError during handler import"""
    pass
