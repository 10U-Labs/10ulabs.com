from unittest.mock import MagicMock, patch
import pytest


class TestGetSupportedAzs:

    def test_returns_empty_set_when_no_offerings(self, find_suitable_subnet):
        mock_ec2 = MagicMock()
        mock_ec2.describe_instance_type_offerings.return_value = {'InstanceTypeOfferings': []}

        result = find_suitable_subnet.get_supported_azs(mock_ec2, ['t4g.large'])

        assert result == set()

    def test_returns_single_az_for_single_instance_type(self, find_suitable_subnet):
        mock_ec2 = MagicMock()
        mock_ec2.describe_instance_type_offerings.return_value = {
            'InstanceTypeOfferings': [{'Location': 'us-east-1a'}]
        }

        result = find_suitable_subnet.get_supported_azs(mock_ec2, ['t4g.large'])

        assert result == {'us-east-1a'}

    def test_returns_multiple_azs_for_single_instance_type(self, find_suitable_subnet):
        mock_ec2 = MagicMock()
        mock_ec2.describe_instance_type_offerings.return_value = {
            'InstanceTypeOfferings': [
                {'Location': 'us-east-1a'},
                {'Location': 'us-east-1b'}
            ]
        }

        result = find_suitable_subnet.get_supported_azs(mock_ec2, ['t4g.large'])

        assert result == {'us-east-1a', 'us-east-1b'}

    def test_returns_union_of_azs_for_multiple_instance_types(self, find_suitable_subnet):
        mock_ec2 = MagicMock()
        mock_ec2.describe_instance_type_offerings.side_effect = [
            {'InstanceTypeOfferings': [{'Location': 'us-east-1a'}]},
            {'InstanceTypeOfferings': [{'Location': 'us-east-1b'}]}
        ]

        result = find_suitable_subnet.get_supported_azs(mock_ec2, ['t4g.large', 't4g.medium'])

        assert result == {'us-east-1a', 'us-east-1b'}

    def test_calls_describe_instance_type_offerings_with_correct_filter(self, find_suitable_subnet):
        mock_ec2 = MagicMock()
        mock_ec2.describe_instance_type_offerings.return_value = {'InstanceTypeOfferings': []}

        find_suitable_subnet.get_supported_azs(mock_ec2, ['t4g.large'])

        mock_ec2.describe_instance_type_offerings.assert_called_once_with(
            LocationType='availability-zone',
            Filters=[{'Name': 'instance-type', 'Values': ['t4g.large']}]
        )


class TestGetSubnetAzMap:

    def test_returns_empty_dict_when_no_subnets_in_supported_azs(self, find_suitable_subnet):
        mock_ec2 = MagicMock()
        mock_ec2.describe_subnets.return_value = {'Subnets': [{'AvailabilityZone': 'us-east-1c'}]}

        result = find_suitable_subnet.get_subnet_az_map(mock_ec2, ['subnet-123'], {'us-east-1a'})

        assert result == {}

    def test_returns_mapping_for_supported_subnet(self, find_suitable_subnet):
        mock_ec2 = MagicMock()
        mock_ec2.describe_subnets.return_value = {'Subnets': [{'AvailabilityZone': 'us-east-1a'}]}

        result = find_suitable_subnet.get_subnet_az_map(mock_ec2, ['subnet-123'], {'us-east-1a'})

        assert result == {'subnet-123': 'us-east-1a'}

    def test_filters_out_unsupported_az_subnets(self, find_suitable_subnet):
        mock_ec2 = MagicMock()
        mock_ec2.describe_subnets.side_effect = [
            {'Subnets': [{'AvailabilityZone': 'us-east-1a'}]},
            {'Subnets': [{'AvailabilityZone': 'us-east-1c'}]}
        ]

        result = find_suitable_subnet.get_subnet_az_map(mock_ec2, ['subnet-123', 'subnet-456'], {'us-east-1a'})

        assert result == {'subnet-123': 'us-east-1a'}

    def test_strips_whitespace_from_subnet_ids(self, find_suitable_subnet):
        mock_ec2 = MagicMock()
        mock_ec2.describe_subnets.return_value = {'Subnets': [{'AvailabilityZone': 'us-east-1a'}]}

        find_suitable_subnet.get_subnet_az_map(mock_ec2, [' subnet-123 '], {'us-east-1a'})

        mock_ec2.describe_subnets.assert_called_once_with(SubnetIds=['subnet-123'])

    def test_returns_multiple_mappings(self, find_suitable_subnet):
        mock_ec2 = MagicMock()
        mock_ec2.describe_subnets.side_effect = [
            {'Subnets': [{'AvailabilityZone': 'us-east-1a'}]},
            {'Subnets': [{'AvailabilityZone': 'us-east-1b'}]}
        ]

        result = find_suitable_subnet.get_subnet_az_map(mock_ec2, ['subnet-123', 'subnet-456'], {'us-east-1a', 'us-east-1b'})

        assert len(result) == 2


class TestGetAzScores:

    def test_returns_scores_for_candidate_azs(self, find_suitable_subnet):
        mock_ec2 = MagicMock()
        mock_ec2.get_spot_placement_scores.return_value = {
            'SpotPlacementScores': [{'AvailabilityZoneId': 'use1-az1', 'Score': 9}]
        }
        mock_ec2.describe_availability_zones.return_value = {
            'AvailabilityZones': [{'ZoneName': 'us-east-1a', 'ZoneId': 'use1-az1'}]
        }

        result = find_suitable_subnet.get_az_scores(mock_ec2, ['t4g.large'], ['us-east-1a'])

        assert result == {'us-east-1a': 9}

    def test_returns_zero_for_missing_az_score(self, find_suitable_subnet):
        mock_ec2 = MagicMock()
        mock_ec2.get_spot_placement_scores.return_value = {'SpotPlacementScores': []}
        mock_ec2.describe_availability_zones.return_value = {
            'AvailabilityZones': [{'ZoneName': 'us-east-1a', 'ZoneId': 'use1-az1'}]
        }

        result = find_suitable_subnet.get_az_scores(mock_ec2, ['t4g.large'], ['us-east-1a'])

        assert result == {'us-east-1a': 0}

    def test_extracts_region_from_az_name(self, find_suitable_subnet):
        mock_ec2 = MagicMock()
        mock_ec2.get_spot_placement_scores.return_value = {'SpotPlacementScores': []}
        mock_ec2.describe_availability_zones.return_value = {'AvailabilityZones': []}

        find_suitable_subnet.get_az_scores(mock_ec2, ['t4g.large'], ['us-west-2a'])

        call_args = mock_ec2.get_spot_placement_scores.call_args
        assert call_args[1]['RegionNames'] == ['us-west-2']

    def test_calls_get_spot_placement_scores_with_correct_params(self, find_suitable_subnet):
        mock_ec2 = MagicMock()
        mock_ec2.get_spot_placement_scores.return_value = {'SpotPlacementScores': []}
        mock_ec2.describe_availability_zones.return_value = {'AvailabilityZones': []}

        find_suitable_subnet.get_az_scores(mock_ec2, ['t4g.large', 't4g.medium'], ['us-east-1a'])

        call_args = mock_ec2.get_spot_placement_scores.call_args
        assert call_args[1]['InstanceTypes'] == ['t4g.large', 't4g.medium']

    def test_handles_multiple_azs(self, find_suitable_subnet):
        mock_ec2 = MagicMock()
        mock_ec2.get_spot_placement_scores.return_value = {
            'SpotPlacementScores': [
                {'AvailabilityZoneId': 'use1-az1', 'Score': 9},
                {'AvailabilityZoneId': 'use1-az2', 'Score': 7}
            ]
        }
        mock_ec2.describe_availability_zones.return_value = {
            'AvailabilityZones': [
                {'ZoneName': 'us-east-1a', 'ZoneId': 'use1-az1'},
                {'ZoneName': 'us-east-1b', 'ZoneId': 'use1-az2'}
            ]
        }

        result = find_suitable_subnet.get_az_scores(mock_ec2, ['t4g.large'], ['us-east-1a', 'us-east-1b'])

        assert len(result) == 2


class TestFindSuitableSubnet:

    def test_returns_none_when_no_supported_azs(self, find_suitable_subnet):
        with patch.object(find_suitable_subnet, 'get_supported_azs', return_value=set()), \
             patch('boto3.client'):

            result = find_suitable_subnet.find_suitable_subnet(['t4g.large'], ['subnet-123'])

            assert result is None

    def test_returns_none_when_no_valid_subnets(self, find_suitable_subnet):
        with patch.object(find_suitable_subnet, 'get_supported_azs', return_value={'us-east-1a'}), \
             patch.object(find_suitable_subnet, 'get_subnet_az_map', return_value={}), \
             patch('boto3.client'):

            result = find_suitable_subnet.find_suitable_subnet(['t4g.large'], ['subnet-123'])

            assert result is None

    def test_returns_highest_scored_az_subnet(self, find_suitable_subnet):
        with patch.object(find_suitable_subnet, 'get_supported_azs', return_value={'us-east-1a', 'us-east-1b'}), \
             patch.object(find_suitable_subnet, 'get_subnet_az_map', return_value={'subnet-123': 'us-east-1a', 'subnet-456': 'us-east-1b'}), \
             patch.object(find_suitable_subnet, 'get_az_scores', return_value={'us-east-1a': 5, 'us-east-1b': 9}), \
             patch('boto3.client'):

            result = find_suitable_subnet.find_suitable_subnet(['t4g.large'], ['subnet-123', 'subnet-456'])

            assert result == 'subnet-456'

    def test_returns_subnet_when_single_option(self, find_suitable_subnet):
        with patch.object(find_suitable_subnet, 'get_supported_azs', return_value={'us-east-1a'}), \
             patch.object(find_suitable_subnet, 'get_subnet_az_map', return_value={'subnet-123': 'us-east-1a'}), \
             patch.object(find_suitable_subnet, 'get_az_scores', return_value={'us-east-1a': 9}), \
             patch('boto3.client'):

            result = find_suitable_subnet.find_suitable_subnet(['t4g.large'], ['subnet-123'])

            assert result == 'subnet-123'


class TestMain:

    def test_check_command_exits_zero_when_subnet_found(self, find_suitable_subnet):
        with patch.object(find_suitable_subnet, 'find_suitable_subnet', return_value='subnet-123'), \
             patch('sys.argv', ['find_suitable_subnet.py', 'check', '--instance-types', '["t4g.large"]', '--subnet-ids', 'subnet-123']):

            with pytest.raises(SystemExit) as exc_info:
                find_suitable_subnet.main()

            assert exc_info.value.code == 0

    def test_check_command_exits_one_when_no_subnet(self, find_suitable_subnet):
        with patch.object(find_suitable_subnet, 'find_suitable_subnet', return_value=None), \
             patch('sys.argv', ['find_suitable_subnet.py', 'check', '--instance-types', '["t4g.large"]', '--subnet-ids', 'subnet-123']):

            with pytest.raises(SystemExit) as exc_info:
                find_suitable_subnet.main()

            assert exc_info.value.code == 1

    def test_get_command_exits_zero_when_subnet_found(self, find_suitable_subnet):
        with patch.object(find_suitable_subnet, 'find_suitable_subnet', return_value='subnet-123'), \
             patch('sys.argv', ['find_suitable_subnet.py', 'get', '--instance-types', '["t4g.large"]', '--subnet-ids', 'subnet-123']), \
             patch('builtins.print'):

            with pytest.raises(SystemExit) as exc_info:
                find_suitable_subnet.main()

            assert exc_info.value.code == 0

    def test_get_command_exits_one_when_no_subnet(self, find_suitable_subnet):
        with patch.object(find_suitable_subnet, 'find_suitable_subnet', return_value=None), \
             patch('sys.argv', ['find_suitable_subnet.py', 'get', '--instance-types', '["t4g.large"]', '--subnet-ids', 'subnet-123']), \
             patch('builtins.print'):

            with pytest.raises(SystemExit) as exc_info:
                find_suitable_subnet.main()

            assert exc_info.value.code == 1

    def test_get_command_prints_subnet_id(self, find_suitable_subnet):
        with patch.object(find_suitable_subnet, 'find_suitable_subnet', return_value='subnet-123'), \
             patch('sys.argv', ['find_suitable_subnet.py', 'get', '--instance-types', '["t4g.large"]', '--subnet-ids', 'subnet-123']), \
             patch('builtins.print') as mock_print:

            with pytest.raises(SystemExit):
                find_suitable_subnet.main()

            mock_print.assert_called_with('subnet-123')

    def test_parses_json_instance_types(self, find_suitable_subnet):
        with patch.object(find_suitable_subnet, 'find_suitable_subnet', return_value='subnet-123') as mock_find, \
             patch('sys.argv', ['find_suitable_subnet.py', 'get', '--instance-types', '["t4g.large","t4g.medium"]', '--subnet-ids', 'subnet-123']), \
             patch('builtins.print'):

            with pytest.raises(SystemExit):
                find_suitable_subnet.main()

            call_args = mock_find.call_args[0]
            assert call_args[0] == ['t4g.large', 't4g.medium']

    def test_parses_comma_separated_subnet_ids(self, find_suitable_subnet):
        with patch.object(find_suitable_subnet, 'find_suitable_subnet', return_value='subnet-123') as mock_find, \
             patch('sys.argv', ['find_suitable_subnet.py', 'get', '--instance-types', '["t4g.large"]', '--subnet-ids', 'subnet-123,subnet-456']), \
             patch('builtins.print'):

            with pytest.raises(SystemExit):
                find_suitable_subnet.main()

            call_args = mock_find.call_args[0]
            assert call_args[1] == ['subnet-123', 'subnet-456']
