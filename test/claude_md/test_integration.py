import boto3


def test_bedrock_client_can_be_created(config):
    client = boto3.client('bedrock-runtime', region_name=config['region'])
    assert client is not None


def test_bedrock_converse_api_is_accessible(bedrock_client, config):
    model_id = config['bedrock']['model_id']
    messages = [{'role': 'user', 'content': [{'text': 'Hello'}]}]
    response = bedrock_client.converse(
        modelId=model_id,
        messages=messages,
        inferenceConfig={'maxTokens': 100}
    )
    assert 'output' in response


def test_bedrock_response_has_expected_structure(bedrock_client, config):
    model_id = config['bedrock']['model_id']
    messages = [{'role': 'user', 'content': [{'text': 'Hello'}]}]
    response = bedrock_client.converse(
        modelId=model_id,
        messages=messages,
        inferenceConfig={'maxTokens': 100}
    )
    assert 'output' in response
    assert 'message' in response['output']
    assert 'content' in response['output']['message']


def test_bedrock_extended_thinking_can_be_enabled(bedrock_client, config):
    model_id = config['bedrock']['model_id']
    max_tokens_reasoning = config['bedrock']['max_tokens_reasoning']
    messages = [{'role': 'user', 'content': [{'text': 'Think about: What is 2+2?'}]}]
    response = bedrock_client.converse(
        modelId=model_id,
        messages=messages,
        inferenceConfig={'maxTokens': 100},
        additionalModelRequestFields={
            'reasoning_config': {
                'type': 'enabled',
                'budget_tokens': max_tokens_reasoning
            }
        }
    )
    assert 'output' in response


def test_bedrock_response_contains_text_block(bedrock_client, config):
    model_id = config['bedrock']['model_id']
    messages = [{'role': 'user', 'content': [{'text': 'Say hello'}]}]
    response = bedrock_client.converse(
        modelId=model_id,
        messages=messages,
        inferenceConfig={'maxTokens': 50}
    )
    content_blocks = response['output']['message']['content']
    text_blocks = [block for block in content_blocks if block.get('type') == 'text']
    assert len(text_blocks) > 0


def test_config_has_required_bedrock_fields(config):
    assert 'bedrock' in config
    assert 'model_id' in config['bedrock']
    assert 'max_tokens' in config['bedrock']
    assert 'max_tokens_reasoning' in config['bedrock']


def test_config_region_is_valid(config):
    assert 'region' in config
    assert isinstance(config['region'], str)
    assert len(config['region']) > 0
