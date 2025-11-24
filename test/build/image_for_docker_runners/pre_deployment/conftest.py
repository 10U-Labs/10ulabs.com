import importlib.util
import os
import sys


sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../src/build/image_for_docker_runners'))
entrypoint_path = os.path.join(os.path.dirname(__file__), '../../../../src/build/image_for_docker_runners/entrypoint.py')
entrypoint_spec = importlib.util.spec_from_file_location("entrypoint", entrypoint_path)
if entrypoint_spec is None or entrypoint_spec.loader is None:
    raise ImportError("Could not load entrypoint module")
entrypoint = importlib.util.module_from_spec(entrypoint_spec)
entrypoint_spec.loader.exec_module(entrypoint)
