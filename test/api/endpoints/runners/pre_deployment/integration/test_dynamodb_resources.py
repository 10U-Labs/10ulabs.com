"""Tests to validate DynamoDB resources exist for runners."""


def test_idempotency_table_exists(dynamodb_client):
    """Verify the idempotency table exists."""
    response = dynamodb_client.list_tables()
    table_names = response.get("TableNames", [])
    idempotency_tables = [t for t in table_names if "idempotency" in t.lower()]
    assert len(idempotency_tables) >= 1, "No idempotency table found"


def test_circuit_breaker_state_table_exists(dynamodb_client):
    """Verify the circuit breaker state table exists."""
    response = dynamodb_client.list_tables()
    table_names = response.get("TableNames", [])
    cb_tables = [t for t in table_names if "circuit-breaker-state" in t.lower()]
    assert len(cb_tables) >= 1, "No circuit breaker state table found"


def test_workflow_runners_table_exists(dynamodb_client):
    """Verify the workflow runners table exists."""
    response = dynamodb_client.list_tables()
    table_names = response.get("TableNames", [])
    wf_tables = [t for t in table_names if "workflow-runners" in t.lower()]
    assert len(wf_tables) >= 1, "No workflow runners table found"


def test_incidents_table_exists(dynamodb_client):
    """Verify the incidents table exists."""
    response = dynamodb_client.list_tables()
    table_names = response.get("TableNames", [])
    incident_tables = [t for t in table_names if "incidents" in t.lower()]
    assert len(incident_tables) >= 1, "No incidents table found"
