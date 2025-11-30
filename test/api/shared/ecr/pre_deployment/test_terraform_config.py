import os


def test_backend_tf_exists(ecr_dir):
    path = os.path.join(ecr_dir, 'backend.tf')
    assert os.path.exists(path)


def test_main_tf_exists(ecr_dir):
    path = os.path.join(ecr_dir, 'main.tf')
    assert os.path.exists(path)


def test_outputs_tf_exists(ecr_dir):
    path = os.path.join(ecr_dir, 'outputs.tf')
    assert os.path.exists(path)


def test_ecr_repository_name_defined(ecr_repository_name):
    assert ecr_repository_name is not None


def test_ecr_repository_name_not_empty(ecr_repository_name):
    assert len(ecr_repository_name) > 0
