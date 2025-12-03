def test_ecs_cluster_exists(ecs_client, config):
    cluster_name = config["cluster_name"]
    response = ecs_client.describe_clusters(clusters=[cluster_name])
    assert len(response['clusters']) == 1


def test_ecs_cluster_is_active(ecs_client, config):
    cluster_name = config["cluster_name"]
    response = ecs_client.describe_clusters(clusters=[cluster_name])
    assert response['clusters'][0]['status'] == 'ACTIVE'
