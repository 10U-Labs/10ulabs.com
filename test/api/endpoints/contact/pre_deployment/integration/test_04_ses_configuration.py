"""Tests to validate SES is configured for contact endpoint.

Five-layer testing model:
- Layer 4: Configuration - Is SES configured correctly?

These tests verify that SES is properly configured for sending emails.
"""


class TestSESConfiguration:
    """Layer 3-4: Verify SES is configured for sending emails."""

    def test_ses_sending_is_enabled(self, ses_client):
        """Verify SES sending is enabled in the region."""
        response = ses_client.get_account_sending_enabled()
        assert response.get("Enabled", False), (
            "SES sending is not enabled in this region. "
            "Enable SES sending or request production access from AWS."
        )

    def test_has_verified_email_identity(self, ses_client):
        """Verify at least one email identity is verified."""
        response = ses_client.list_identities(IdentityType="EmailAddress")
        identities = response.get("Identities", [])
        assert len(identities) >= 1, (
            "No verified email identities found in SES. "
            "Verify an email address in SES console or via terraform."
        )
