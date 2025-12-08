"""Unit tests for has_excluded_tags functionality."""


class TestHasExcludedTagsReturnsFalse:
    """Tests for has_excluded_tags when returning False."""

    def test_returns_false_when_exclude_tags_is_none(self, cleanup):
        """Test that False is returned when exclude_tags is None."""
        resource_tags = [{'Key': 'ManagedBy', 'Value': 'terraform'}]

        result = cleanup.has_excluded_tags(resource_tags, None)

        assert result is False

    def test_returns_false_when_exclude_tags_is_empty(self, cleanup):
        """Test that False is returned when exclude_tags is empty."""
        resource_tags = [{'Key': 'ManagedBy', 'Value': 'terraform'}]

        result = cleanup.has_excluded_tags(resource_tags, {})

        assert result is False

    def test_returns_false_when_resource_tags_is_none(self, cleanup):
        """Test that False is returned when resource_tags is None."""
        exclude_tags = {'ManagedBy': 'terraform'}

        result = cleanup.has_excluded_tags(None, exclude_tags)

        assert result is False

    def test_returns_false_when_resource_tags_is_empty(self, cleanup):
        """Test that False is returned when resource_tags is empty."""
        exclude_tags = {'ManagedBy': 'terraform'}

        result = cleanup.has_excluded_tags([], exclude_tags)

        assert result is False

    def test_returns_false_when_no_matching_tag(self, cleanup):
        """Test that False is returned when no matching tag."""
        resource_tags = [{'Key': 'Purpose', 'Value': 'runner'}]
        exclude_tags = {'ManagedBy': 'terraform'}

        result = cleanup.has_excluded_tags(resource_tags, exclude_tags)

        assert result is False

    def test_returns_false_when_key_matches_but_value_differs(self, cleanup):
        """Test that False is returned when key matches but value differs."""
        resource_tags = [{'Key': 'ManagedBy', 'Value': 'manual'}]
        exclude_tags = {'ManagedBy': 'terraform'}

        result = cleanup.has_excluded_tags(resource_tags, exclude_tags)

        assert result is False


class TestHasExcludedTagsReturnsTrue:
    """Tests for has_excluded_tags when returning True."""

    def test_returns_true_when_tag_matches(self, cleanup):
        """Test that True is returned when tag matches."""
        resource_tags = [{'Key': 'ManagedBy', 'Value': 'terraform'}]
        exclude_tags = {'ManagedBy': 'terraform'}

        result = cleanup.has_excluded_tags(resource_tags, exclude_tags)

        assert result is True

    def test_returns_true_when_any_exclude_tag_matches(self, cleanup):
        """Test that True is returned when any exclude tag matches."""
        resource_tags = [{'Key': 'Purpose', 'Value': 'api-infrastructure'}]
        exclude_tags = {
            'ManagedBy': 'terraform',
            'Purpose': 'api-infrastructure',
        }

        result = cleanup.has_excluded_tags(resource_tags, exclude_tags)

        assert result is True

    def test_returns_true_when_first_exclude_tag_matches(self, cleanup):
        """Test that True is returned when first exclude tag matches."""
        resource_tags = [{'Key': 'ManagedBy', 'Value': 'terraform'}]
        exclude_tags = {
            'ManagedBy': 'terraform',
            'Purpose': 'api-infrastructure',
        }

        result = cleanup.has_excluded_tags(resource_tags, exclude_tags)

        assert result is True

    def test_returns_true_with_multiple_resource_tags(self, cleanup):
        """Test that True is returned with multiple resource tags."""
        resource_tags = [
            {'Key': 'Name', 'Value': 'my-resource'},
            {'Key': 'ManagedBy', 'Value': 'terraform'},
        ]
        exclude_tags = {'ManagedBy': 'terraform'}

        result = cleanup.has_excluded_tags(resource_tags, exclude_tags)

        assert result is True
