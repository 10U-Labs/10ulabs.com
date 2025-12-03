import json
from typing import Any, Dict

SOC_CONFIG = {
    'issue_width': 4,
    'rob_entries': 128,
    'l1_size_kb': 64,
    'l2_size_kb': 512,
    'clock_ghz': 3.2
}

INSTRUCTION_COUNT = 1_000_000_000

PERSONA_CONFIG = {
    'riscv': {
        'base_cpi': 1.2,
        'tri_mode_penalty': 0.92
    },
    'x86_64': {
        'base_cpi': 1.1,
        'tri_mode_penalty': 0.88
    },
    'arm64': {
        'base_cpi': 1.15,
        'tri_mode_penalty': 0.90
    }
}

VALID_PERSONAS = frozenset(PERSONA_CONFIG.keys())


def json_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET,POST,DELETE,OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type,x-api-key,x-test-mode'
        },
        'body': json.dumps(body)
    }


def error_response(status_code: int, error: str, details: str | None = None) -> Dict[str, Any]:
    body: Dict[str, Any] = {'success': False, 'error': error}
    if details:
        body['details'] = details
    return json_response(status_code, body)


def parse_body(event: Dict[str, Any]) -> Dict[str, Any]:
    body = event.get('body', {})
    result = json.loads(body) if isinstance(body, str) else body
    return result


def compute_simulation(persona: str) -> Dict[str, Any]:
    config = PERSONA_CONFIG[persona]
    base_cpi = config['base_cpi']
    penalty = config['tri_mode_penalty']

    native_ipc = 1.0 / base_cpi
    native_runtime = INSTRUCTION_COUNT / (native_ipc * SOC_CONFIG['clock_ghz'] * 1e9)

    tri_mode_ipc = native_ipc * penalty
    tri_mode_runtime = INSTRUCTION_COUNT / (tri_mode_ipc * SOC_CONFIG['clock_ghz'] * 1e9)

    relative_slowdown = tri_mode_runtime / native_runtime

    result = {
        'success': True,
        'persona': persona,
        'soc_config': SOC_CONFIG,
        'instruction_count': INSTRUCTION_COUNT,
        'native_core': {
            'ipc': native_ipc,
            'runtime_seconds': native_runtime
        },
        'tri_mode_core': {
            'ipc': tri_mode_ipc,
            'runtime_seconds': tri_mode_runtime
        },
        'relative_slowdown': relative_slowdown
    }
    return result


def handle_simulation_soc_post(event: Dict[str, Any]) -> Dict[str, Any]:
    try:
        body = parse_body(event)
        persona = body.get('persona')

        if not persona:
            response = error_response(400, 'Missing required field: persona')
        elif persona not in VALID_PERSONAS:
            valid_list = ', '.join(sorted(VALID_PERSONAS))
            response = error_response(
                400,
                f'Invalid persona: {persona}',
                f'Valid personas are: {valid_list}'
            )
        else:
            result = compute_simulation(persona)
            response = json_response(200, result)
    except json.JSONDecodeError:
        response = error_response(400, 'Invalid JSON in request body')
    except (ValueError, KeyError) as exc:
        response = error_response(500, 'Internal server error', str(exc))
    return response


ROUTE_MAP = {
    ('/v1/simultation-soc', 'POST'): handle_simulation_soc_post,
}


def handler(event, _context):
    method = event.get('httpMethod', '')
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET,POST,DELETE,OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type,x-api-key,x-test-mode'
            },
            'body': ''
        }

    path = event.get('path', '')
    route_handler = ROUTE_MAP.get((path, method))
    if route_handler:
        response = route_handler(event)
    else:
        response = json_response(404, {'error': 'Not found'})
    return response
