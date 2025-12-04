import json
import math
from typing import Any, Dict

SOC_CONFIG = {
    'issue_width': 3,
    'rob_entries': 126,
    'l1_size_kb': 8,
    'l2_size_kb': 512,
    'clock_ghz': 3.0
}

INSTRUCTION_COUNT = 1_000_000_000

ISA_CONFIG = {
    'riscv': {
        'decode_efficiency': 0.95,
        'inst_expansion': 1.15,
        'branch_penalty_cycles': 12,
        'branch_mispredict_rate': 0.03,
    },
    'x86_64': {
        'decode_efficiency': 0.82,
        'inst_expansion': 1.0,
        'branch_penalty_cycles': 15,
        'branch_mispredict_rate': 0.035,
    },
    'arm64': {
        'decode_efficiency': 0.92,
        'inst_expansion': 1.08,
        'branch_penalty_cycles': 11,
        'branch_mispredict_rate': 0.028,
    }
}

TRI_MODE_OVERHEAD = {
    'decode_penalty': 0.88,
    'execution_penalty': 0.94,
    'frontend_penalty': 0.92,
}

L1_MISS_LATENCY_CYCLES = 12
L2_MISS_LATENCY_CYCLES = 150
MEMORY_ACCESS_RATE = 0.25

VALID_PERSONAS = frozenset(ISA_CONFIG.keys())


def estimate_cache_miss_rates(l1_size_kb: int, l2_size_kb: int) -> Dict[str, float]:
    l1_miss_rate = 0.15 * math.pow(32 / l1_size_kb, 0.7)
    l1_miss_rate = min(0.5, max(0.01, l1_miss_rate))

    l2_miss_rate = 0.08 * math.pow(512 / l2_size_kb, 0.5)
    l2_miss_rate = min(0.4, max(0.005, l2_miss_rate))

    result = {
        'l1_miss_rate': l1_miss_rate,
        'l2_miss_rate': l2_miss_rate,
    }
    return result


def estimate_rob_limited_ilp(rob_entries: int) -> float:
    base_ilp = math.sqrt(rob_entries) * 0.6
    result = min(base_ilp, 8.0)
    return result


def compute_memory_stall_cpi(cache_stats: Dict[str, float]) -> float:
    l1_miss_rate = cache_stats['l1_miss_rate']
    l2_miss_rate = cache_stats['l2_miss_rate']

    l1_stall = MEMORY_ACCESS_RATE * l1_miss_rate * L1_MISS_LATENCY_CYCLES
    l2_stall = MEMORY_ACCESS_RATE * l1_miss_rate * l2_miss_rate * L2_MISS_LATENCY_CYCLES

    result = l1_stall + l2_stall
    return result


def compute_branch_stall_cpi(isa_config: Dict[str, Any]) -> float:
    branch_rate = 0.15
    mispredict_rate = isa_config['branch_mispredict_rate']
    penalty = isa_config['branch_penalty_cycles']

    result = branch_rate * mispredict_rate * penalty
    return result


def compute_native_ipc(soc_config: Dict[str, Any], isa: str) -> Dict[str, Any]:
    isa_config = ISA_CONFIG[isa]

    cache_stats = estimate_cache_miss_rates(
        soc_config['l1_size_kb'],
        soc_config['l2_size_kb']
    )

    rob_ilp = estimate_rob_limited_ilp(soc_config['rob_entries'])

    issue_limited_ipc = min(soc_config['issue_width'], rob_ilp)

    decode_ipc = issue_limited_ipc * isa_config['decode_efficiency']

    memory_stall_cpi = compute_memory_stall_cpi(cache_stats)
    branch_stall_cpi = compute_branch_stall_cpi(isa_config)
    total_stall_cpi = memory_stall_cpi + branch_stall_cpi

    effective_cpi = (1.0 / decode_ipc) + total_stall_cpi
    effective_ipc = 1.0 / effective_cpi

    result = {
        'ipc': effective_ipc,
        'cache_stats': cache_stats,
        'rob_ilp': rob_ilp,
        'memory_stall_cpi': memory_stall_cpi,
        'branch_stall_cpi': branch_stall_cpi,
    }
    return result


def compute_tri_mode_ipc(native_result: Dict[str, Any], isa: str) -> Dict[str, Any]:
    native_ipc = native_result['ipc']

    combined_penalty = (
        TRI_MODE_OVERHEAD['decode_penalty'] *
        TRI_MODE_OVERHEAD['execution_penalty'] *
        TRI_MODE_OVERHEAD['frontend_penalty']
    )

    tri_mode_ipc = native_ipc * combined_penalty

    result = {
        'ipc': tri_mode_ipc,
        'overhead_factor': combined_penalty,
    }
    return result


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
    native_result = compute_native_ipc(SOC_CONFIG, persona)
    tri_mode_result = compute_tri_mode_ipc(native_result, persona)

    native_ipc = native_result['ipc']
    tri_mode_ipc = tri_mode_result['ipc']

    cycles_per_second = SOC_CONFIG['clock_ghz'] * 1e9
    native_runtime = INSTRUCTION_COUNT / (native_ipc * cycles_per_second)
    tri_mode_runtime = INSTRUCTION_COUNT / (tri_mode_ipc * cycles_per_second)

    relative_slowdown = tri_mode_runtime / native_runtime

    result = {
        'success': True,
        'persona': persona,
        'soc_config': SOC_CONFIG,
        'instruction_count': INSTRUCTION_COUNT,
        'native_core': {
            'ipc': native_ipc,
            'runtime_seconds': native_runtime,
            'cache_stats': native_result['cache_stats'],
            'rob_ilp': native_result['rob_ilp'],
            'memory_stall_cpi': native_result['memory_stall_cpi'],
            'branch_stall_cpi': native_result['branch_stall_cpi'],
        },
        'tri_mode_core': {
            'ipc': tri_mode_ipc,
            'runtime_seconds': tri_mode_runtime,
            'overhead_factor': tri_mode_result['overhead_factor'],
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
    ('/v1/simulation-soc', 'POST'): handle_simulation_soc_post,
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
