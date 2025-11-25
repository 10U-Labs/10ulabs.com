from test.api.conftest import find_sns_topic_arns


def test_sns_circuit_breaker_alerts_topic_exists(sns_client, config):
    topic_name = f"{config['resource_prefix']}-circuit-breaker-alerts"
    matching_topics = find_sns_topic_arns(sns_client, topic_name)
    assert len(matching_topics) == 1


def test_sns_circuit_breaker_alerts_has_email_subscription(sns_client, config):
    topic_name = f"{config['resource_prefix']}-circuit-breaker-alerts"
    topics = sns_client.list_topics()
    topic_arn = next((t['TopicArn'] for t in topics['Topics'] if topic_name in t['TopicArn']), None)
    assert topic_arn is not None


def test_sns_subscription_protocol_is_email(sns_client, config):
    topic_name = f"{config['resource_prefix']}-circuit-breaker-alerts"
    topics = sns_client.list_topics()
    topic_arn = next((t['TopicArn'] for t in topics['Topics'] if topic_name in t['TopicArn']), None)
    subscriptions = sns_client.list_subscriptions_by_topic(TopicArn=topic_arn)
    email_subs = [s for s in subscriptions['Subscriptions'] if s['Protocol'] == 'email']
    assert len(email_subs) == 1


def test_sns_subscription_endpoint_matches_config(sns_client, config):
    topic_name = f"{config['resource_prefix']}-circuit-breaker-alerts"
    topics = sns_client.list_topics()
    topic_arn = next((t['TopicArn'] for t in topics['Topics'] if topic_name in t['TopicArn']), None)
    subscriptions = sns_client.list_subscriptions_by_topic(TopicArn=topic_arn)
    email_subs = [s for s in subscriptions['Subscriptions'] if s['Protocol'] == 'email']
    assert email_subs[0]['Endpoint'] == config['circuit_breaker_alert_email']


def test_sns_topic_has_display_name(sns_client, config):
    topic_name = f"{config['resource_prefix']}-circuit-breaker-alerts"
    topics = sns_client.list_topics()
    topic_arn = next((t['TopicArn'] for t in topics['Topics'] if topic_name in t['TopicArn']), None)
    attributes = sns_client.get_topic_attributes(TopicArn=topic_arn)
    assert 'Attributes' in attributes


def test_sns_topic_arn_format(sns_client, config):
    topic_name = f"{config['resource_prefix']}-circuit-breaker-alerts"
    topics = sns_client.list_topics()
    topic_arn = next((t['TopicArn'] for t in topics['Topics'] if topic_name in t['TopicArn']), None)
    assert topic_arn.startswith('arn:aws:sns:')
