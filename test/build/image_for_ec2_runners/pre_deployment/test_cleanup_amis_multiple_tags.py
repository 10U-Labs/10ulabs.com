class TestCleanupAmisMultipleTagsOrLogic:

    def test_queries_for_each_tag(self, cleanup, mock_ec2_client, make_ami_cleanup_params):
        mock_ec2_client.describe_images.return_value = {'Images': []}
        tags = {'Purpose': 'test', 'Environment': 'dev'}

        cleanup.cleanup_amis(mock_ec2_client, make_ami_cleanup_params(cleanup, tags=tags))

        assert mock_ec2_client.describe_images.call_count == 2

    def test_deduplicates_amis_matched_by_multiple_tags(self, cleanup, mock_ec2_client, make_ami_cleanup_params):
        mock_ec2_client.describe_images.side_effect = [
            {'Images': [{'ImageId': 'ami-123', 'Name': 'test', 'BlockDeviceMappings': []}]},
            {'Images': [{'ImageId': 'ami-123', 'Name': 'test', 'BlockDeviceMappings': []}]}
        ]
        tags = {'Purpose': 'test', 'Environment': 'dev'}

        count, _ = cleanup.cleanup_amis(mock_ec2_client, make_ami_cleanup_params(cleanup, tags=tags))

        assert count == 1

    def test_collects_amis_from_all_tag_queries(self, cleanup, mock_ec2_client, make_ami_cleanup_params):
        mock_ec2_client.describe_images.side_effect = [
            {'Images': [{'ImageId': 'ami-123', 'Name': 'test1', 'BlockDeviceMappings': []}]},
            {'Images': [{'ImageId': 'ami-456', 'Name': 'test2', 'BlockDeviceMappings': []}]}
        ]
        tags = {'Purpose': 'test', 'Environment': 'dev'}

        count, _ = cleanup.cleanup_amis(mock_ec2_client, make_ami_cleanup_params(cleanup, tags=tags))

        assert count == 2


class TestCleanupInstancesMultipleTagsOrLogic:

    def test_queries_for_each_tag(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_instances.return_value = {'Reservations': []}
        tags = {'Purpose': 'test', 'Environment': 'dev'}

        cleanup.cleanup_instances(mock_ec2_client, False, tags)

        assert mock_ec2_client.describe_instances.call_count == 2

    def test_deduplicates_instances_matched_by_multiple_tags(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_instances.side_effect = [
            {'Reservations': [{'Instances': [{'InstanceId': 'i-123'}]}]},
            {'Reservations': [{'Instances': [{'InstanceId': 'i-123'}]}]}
        ]
        tags = {'Purpose': 'test', 'Environment': 'dev'}

        count = cleanup.cleanup_instances(mock_ec2_client, False, tags)

        assert count == 1

    def test_collects_instances_from_all_tag_queries(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_instances.side_effect = [
            {'Reservations': [{'Instances': [{'InstanceId': 'i-123'}]}]},
            {'Reservations': [{'Instances': [{'InstanceId': 'i-456'}]}]}
        ]
        tags = {'Purpose': 'test', 'Environment': 'dev'}

        count = cleanup.cleanup_instances(mock_ec2_client, False, tags)

        assert count == 2


class TestCleanupSecurityGroupsMultipleTagsOrLogic:

    def test_queries_for_each_tag(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_security_groups.return_value = {'SecurityGroups': []}
        tags = {'Purpose': 'test', 'Environment': 'dev'}

        cleanup.cleanup_security_groups(mock_ec2_client, False, tags)

        assert mock_ec2_client.describe_security_groups.call_count == 2

    def test_deduplicates_security_groups_matched_by_multiple_tags(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_security_groups.side_effect = [
            {'SecurityGroups': [{'GroupId': 'sg-123', 'GroupName': 'test'}]},
            {'SecurityGroups': [{'GroupId': 'sg-123', 'GroupName': 'test'}]}
        ]
        tags = {'Purpose': 'test', 'Environment': 'dev'}

        count = cleanup.cleanup_security_groups(mock_ec2_client, False, tags)

        assert count == 1

    def test_collects_security_groups_from_all_tag_queries(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_security_groups.side_effect = [
            {'SecurityGroups': [{'GroupId': 'sg-123', 'GroupName': 'test1'}]},
            {'SecurityGroups': [{'GroupId': 'sg-456', 'GroupName': 'test2'}]}
        ]
        tags = {'Purpose': 'test', 'Environment': 'dev'}

        count = cleanup.cleanup_security_groups(mock_ec2_client, False, tags)

        assert count == 2


class TestCleanupKeyPairsMultipleTagsOrLogic:

    def test_queries_for_each_tag(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_key_pairs.return_value = {'KeyPairs': []}
        tags = {'Purpose': 'test', 'Environment': 'dev'}

        cleanup.cleanup_key_pairs(mock_ec2_client, False, tags)

        assert mock_ec2_client.describe_key_pairs.call_count == 2

    def test_deduplicates_key_pairs_matched_by_multiple_tags(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_key_pairs.side_effect = [
            {'KeyPairs': [{'KeyName': 'ami-builder-123'}]},
            {'KeyPairs': [{'KeyName': 'ami-builder-123'}]}
        ]
        tags = {'Purpose': 'test', 'Environment': 'dev'}

        count = cleanup.cleanup_key_pairs(mock_ec2_client, False, tags)

        assert count == 1

    def test_collects_key_pairs_from_all_tag_queries(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_key_pairs.side_effect = [
            {'KeyPairs': [{'KeyName': 'ami-builder-123'}]},
            {'KeyPairs': [{'KeyName': 'ami-builder-456'}]}
        ]
        tags = {'Purpose': 'test', 'Environment': 'dev'}

        count = cleanup.cleanup_key_pairs(mock_ec2_client, False, tags)

        assert count == 2


class TestCleanupLaunchTemplatesMultipleTagsOrLogic:

    def test_queries_for_each_tag(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_launch_templates.return_value = {'LaunchTemplates': []}
        tags = {'Purpose': 'test', 'Environment': 'dev'}

        cleanup.cleanup_launch_templates(mock_ec2_client, False, tags)

        assert mock_ec2_client.describe_launch_templates.call_count == 2

    def test_deduplicates_launch_templates_matched_by_multiple_tags(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_launch_templates.side_effect = [
            {'LaunchTemplates': [{'LaunchTemplateId': 'lt-123', 'LaunchTemplateName': 'test'}]},
            {'LaunchTemplates': [{'LaunchTemplateId': 'lt-123', 'LaunchTemplateName': 'test'}]}
        ]
        tags = {'Purpose': 'test', 'Environment': 'dev'}

        count = cleanup.cleanup_launch_templates(mock_ec2_client, False, tags)

        assert count == 1

    def test_collects_launch_templates_from_all_tag_queries(self, cleanup, mock_ec2_client):
        mock_ec2_client.describe_launch_templates.side_effect = [
            {'LaunchTemplates': [{'LaunchTemplateId': 'lt-123', 'LaunchTemplateName': 'test1'}]},
            {'LaunchTemplates': [{'LaunchTemplateId': 'lt-456', 'LaunchTemplateName': 'test2'}]}
        ]
        tags = {'Purpose': 'test', 'Environment': 'dev'}

        count = cleanup.cleanup_launch_templates(mock_ec2_client, False, tags)

        assert count == 2
