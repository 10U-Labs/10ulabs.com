class TestHasExcludedTagsReturnsFalse:

    def test_returns_false_when_exclude_tags_is_none(self, cleanup):
        resource_tags = [{'Key': 'ManagedBy', 'Value': 'terraform'}]

        result = cleanup.has_excluded_tags(resource_tags, None)

        assert result is False

    def test_returns_false_when_exclude_tags_is_empty(self, cleanup):
        resource_tags = [{'Key': 'ManagedBy', 'Value': 'terraform'}]

        result = cleanup.has_excluded_tags(resource_tags, {})

        assert result is False

    def test_returns_false_when_resource_tags_is_none(self, cleanup):
        exclude_tags = {'ManagedBy': 'terraform'}

        result = cleanup.has_excluded_tags(None, exclude_tags)

        assert result is False

    def test_returns_false_when_resource_tags_is_empty(self, cleanup):
        exclude_tags = {'ManagedBy': 'terraform'}

        result = cleanup.has_excluded_tags([], exclude_tags)

        assert result is False

    def test_returns_false_when_no_matching_tag(self, cleanup):
        resource_tags = [{'Key': 'Purpose', 'Value': 'runner'}]
        exclude_tags = {'ManagedBy': 'terraform'}

        result = cleanup.has_excluded_tags(resource_tags, exclude_tags)

        assert result is False

    def test_returns_false_when_key_matches_but_value_differs(self, cleanup):
        resource_tags = [{'Key': 'ManagedBy', 'Value': 'manual'}]
        exclude_tags = {'ManagedBy': 'terraform'}

        result = cleanup.has_excluded_tags(resource_tags, exclude_tags)

        assert result is False


class TestHasExcludedTagsReturnsTrue:

    def test_returns_true_when_tag_matches(self, cleanup):
        resource_tags = [{'Key': 'ManagedBy', 'Value': 'terraform'}]
        exclude_tags = {'ManagedBy': 'terraform'}

        result = cleanup.has_excluded_tags(resource_tags, exclude_tags)

        assert result is True

    def test_returns_true_when_any_exclude_tag_matches(self, cleanup):
        resource_tags = [{'Key': 'Purpose', 'Value': 'api-infrastructure'}]
        exclude_tags = {'ManagedBy': 'terraform', 'Purpose': 'api-infrastructure'}

        result = cleanup.has_excluded_tags(resource_tags, exclude_tags)

        assert result is True

    def test_returns_true_when_first_exclude_tag_matches(self, cleanup):
        resource_tags = [{'Key': 'ManagedBy', 'Value': 'terraform'}]
        exclude_tags = {'ManagedBy': 'terraform', 'Purpose': 'api-infrastructure'}

        result = cleanup.has_excluded_tags(resource_tags, exclude_tags)

        assert result is True

    def test_returns_true_with_multiple_resource_tags(self, cleanup):
        resource_tags = [
            {'Key': 'Name', 'Value': 'my-resource'},
            {'Key': 'ManagedBy', 'Value': 'terraform'}
        ]
        exclude_tags = {'ManagedBy': 'terraform'}

        result = cleanup.has_excluded_tags(resource_tags, exclude_tags)

        assert result is True
