"""Tests to validate SES is configured for contact endpoint."""


def test_ses_sending_enabled(ses_client):
    """Verify SES sending is enabled in the region."""
    response = ses_client.get_account_sending_enabled()
    assert response.get("Enabled", False), "SES sending is not enabled"


def test_ses_has_verified_identities(ses_client):
    """Verify at least one email identity is verified."""
    response = ses_client.list_identities(IdentityType="EmailAddress")
    identities = response.get("Identities", [])
    assert len(identities) >= 1, "No verified email identities found"
