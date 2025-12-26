"""Pytest fixtures for bootstrap pre-deployment integration tests.

Bootstrap Pre-Deployment Layers:
- Layer 1: Contracts (test_01_contracts.py) - Cross-file compatibility, no AWS calls
- Layer 2: Authentication (test_01_authentication.py) - AWS credentials valid
- Layer 3: Authorization (test_02_authorization.py) - Permission to inspect state bucket
- Layer 4: State (test_03_state.py) - Terraform state matches AWS reality

Layers 5-7 Exception:
Bootstrap is self-bootstrapping - it creates its own prerequisites. Layers 5-7
(Existence, Configuration, Capability) test prerequisite resources created by
OTHER workflows, which don't exist for bootstrap. Therefore, these layers are
not applicable here.
"""
pytest_plugins = ['test_fixtures.aws']
