import json
import math
import os
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional, cast

# Google OAuth Client ID - set via environment variable
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')

SOC_CONFIG = {
    'issue_width': 3,
    'backend_dispatch_width': 3,
    'rob_entries': 128,
    'int_phys_regs': 192,
    'fp_vec_phys_regs': 160,
    'load_queue_entries': 64,
    'store_queue_entries': 64,
    'l1i_size_kb': 32,
    'l1d_size_kb': 32,
    'l2_size_kb': 512,
    'clock_ghz': 1.5,
    'pipeline_depth_estimate': 14,
    'process_node_nm': 130,
    'ddr_channels': 2,
    'ddr_generation': 'DDR4'
}

PACKAGE_CONFIG = {
    'size_mm': 40,
    'pitch_mm': 0.8,
    'total_balls': 2500,
    'signal_to_ground_ratio': '1:1',
    'exit_rows': 3,
    'available_signals': 282,
    'gpio_count': 8
}

EXECUTION_UNITS = {
    'int_alus': 3,
    'int_mul_div': 1,
    'fp_vec_units': 2,
    'load_units': 2,
    'store_units': 1
}

LATENCIES = {
    'int_alu': 1,
    'branch': 1,
    'int_mul': 3,
    'int_div': 16,
    'fp_add_mul': 4,
    'fp_div': 16,
    'l1d_hit': 4,
    'l2_hit': 14,
    'memory': 124,
    'branch_mispredict': 12
}

INSTRUCTION_COUNT = 1_000_000_000

TRIMODE_OVERHEAD_PARAMS = {
    'riscv': {
        'flags_live_rate': 0.0,
        'flags_uops_per_live': 0,
        'fence_per_store': False,
        'extra_decode_stages': 0
    },
    'x86_64': {
        'flags_live_rate': 0.25,
        'flags_uops_per_live': 0.15,
        'fence_per_store': False,
        'extra_decode_stages': 0
    },
    'arm64': {
        'flags_live_rate': 0.16,
        'flags_uops_per_live': 0.1,
        'fence_per_store': False,
        'extra_decode_stages': 0
    }
}

FENCE_LATENCY_CYCLES = 6

STORE_BUFFER_ENTRIES = 32

SPEC_TRANSLATION_RANGES = {
    'riscv': {
        'alu': (1, 1),
        'load': (1, 1),
        'store': (1, 1),
        'branch': (1, 1),
        'fp_vec': (1, 1),
        'complex': (1, 2),
    },
    'x86_64': {
        'alu': (1, 2),
        'load': (1, 2),
        'store': (1, 2),
        'branch': (1, 1),
        'fp_vec': (2, 3),
        'complex': (4, 8),
    },
    'arm64': {
        'alu': (1, 1),
        'load': (1, 1),
        'store': (1, 1),
        'branch': (1, 1),
        'fp_vec': (1, 2),
        'complex': (2, 3),
    }
}


def derive_translation_uops(ranges: Dict[str, tuple]) -> Dict[str, float]:
    result = {}
    for category, (low, high) in ranges.items():
        result[category] = (low + high) / 2.0
    return result


TRANSLATION_UOPS = {
    persona: derive_translation_uops(ranges)
    for persona, ranges in SPEC_TRANSLATION_RANGES.items()
}


def compute_flags_overhead_uops(persona: str, instr_count: int) -> float:
    params = TRIMODE_OVERHEAD_PARAMS[persona]
    live_rate = params['flags_live_rate']
    uops_per_live = params['flags_uops_per_live']
    result = instr_count * live_rate * uops_per_live
    return result


def compute_fence_stall_cycles(persona: str, store_count: float) -> float:
    params = TRIMODE_OVERHEAD_PARAMS[persona]
    stall_cycles = 0.0
    if params['fence_per_store']:
        stores_between_fences = STORE_BUFFER_ENTRIES
        fence_count = store_count / stores_between_fences
        stall_cycles = fence_count * FENCE_LATENCY_CYCLES
    result = stall_cycles
    return result


def compute_trimode_mispredict_penalty(persona: str) -> float:
    params = TRIMODE_OVERHEAD_PARAMS[persona]
    base_penalty = LATENCIES['branch_mispredict']
    extra_stages = params['extra_decode_stages']
    result = float(base_penalty + extra_stages)
    return result


def compute_adjusted_uop_stats(persona: str, instr_count: int) -> Dict[str, Any]:
    uop_stats = compute_uop_counts(persona, instr_count)
    flags_uops = compute_flags_overhead_uops(persona, instr_count)
    total_uops_with_flags = uop_stats['total_uops'] + flags_uops
    avg_uops_with_flags = total_uops_with_flags / instr_count
    adjusted = dict(uop_stats)
    adjusted['total_uops'] = total_uops_with_flags
    adjusted['avg_uops_per_instr'] = avg_uops_with_flags
    result = adjusted
    return result


def compute_trimode_effective_ipc(ipc_raw: float, fence_stall_cycles: float, instr_count: int) -> float:
    base_cycles = instr_count / ipc_raw
    total_cycles = base_cycles + fence_stall_cycles
    result = instr_count / total_cycles
    return result

WORKLOADS = {
    'riscv': {
        'alu_fraction': 0.43,
        'load_fraction': 0.22,
        'store_fraction': 0.10,
        'branch_fraction': 0.18,
        'fp_vec_fraction': 0.05,
        'complex_fraction': 0.02,
        'avg_bytes_per_instr': 3.6,
        'branch_mispredict_rate': 0.025,
        'l1d_hit_rate': 0.92,
        'l2_hit_rate': 0.88
    },
    'x86_64': {
        'alu_fraction': 0.43,
        'load_fraction': 0.22,
        'store_fraction': 0.10,
        'branch_fraction': 0.18,
        'fp_vec_fraction': 0.05,
        'complex_fraction': 0.02,
        'avg_bytes_per_instr': 4.0,
        'branch_mispredict_rate': 0.025,
        'l1d_hit_rate': 0.92,
        'l2_hit_rate': 0.88
    },
    'arm64': {
        'alu_fraction': 0.43,
        'load_fraction': 0.22,
        'store_fraction': 0.10,
        'branch_fraction': 0.18,
        'fp_vec_fraction': 0.05,
        'complex_fraction': 0.02,
        'avg_bytes_per_instr': 4.0,
        'branch_mispredict_rate': 0.025,
        'l1d_hit_rate': 0.92,
        'l2_hit_rate': 0.88
    }
}

VALID_PERSONAS = frozenset(WORKLOADS.keys())


def compute_uop_counts_with_translation(workload: Dict[str, Any], translation: Dict[str, float],
                                        instr_count: int) -> Dict[str, Any]:
    categories = ['alu', 'load', 'store', 'branch', 'fp_vec', 'complex']
    uops = {cat: instr_count * workload[f'{cat}_fraction'] * translation[cat] for cat in categories}
    total = sum(uops.values())
    result = {
        'alu_uops': uops['alu'],
        'load_uops': uops['load'],
        'store_uops': uops['store'],
        'branch_uops': uops['branch'],
        'fp_vec_uops': uops['fp_vec'],
        'complex_uops': uops['complex'],
        'total_uops': total,
        'avg_uops_per_instr': total / instr_count
    }
    return result


def compute_uop_counts(persona: str, instr_count: int) -> Dict[str, Any]:
    result = compute_uop_counts_with_translation(WORKLOADS[persona], TRANSLATION_UOPS[persona], instr_count)
    return result


def compute_frontend_ipc(persona: str, uop_stats: Dict[str, Any]) -> Dict[str, Any]:
    workload = WORKLOADS[persona]
    fetch_bytes_per_cycle = 16.0
    issue_width = float(cast(int, SOC_CONFIG['issue_width']))
    avg_bytes = float(workload['avg_bytes_per_instr'])
    avg_uops = float(uop_stats['avg_uops_per_instr'])
    fetch_limited = fetch_bytes_per_cycle / avg_bytes
    decode_limited = issue_width
    uop_limited = issue_width / avg_uops
    ipc_frontend = min(fetch_limited, decode_limited, uop_limited)
    result = {
        'ipc_frontend': ipc_frontend,
        'fetch_limited_ipc': fetch_limited,
        'decode_limited_ipc': decode_limited,
        'uop_emission_limited_ipc': uop_limited
    }
    return result


def compute_resource_limited_upc(uop_stats: Dict[str, Any]) -> float:
    total = float(uop_stats['total_uops'])
    alu_frac = (float(uop_stats['alu_uops']) + float(uop_stats['branch_uops']) + float(uop_stats['complex_uops']) * 0.5) / total
    load_frac = float(uop_stats['load_uops']) / total
    store_frac = float(uop_stats['store_uops']) / total
    fp_frac = (float(uop_stats['fp_vec_uops']) + float(uop_stats['complex_uops']) * 0.5) / total
    limits: List[float] = [
        float(EXECUTION_UNITS['int_alus']) / alu_frac if alu_frac > 0 else float('inf'),
        float(EXECUTION_UNITS['load_units']) / load_frac if load_frac > 0 else float('inf'),
        float(EXECUTION_UNITS['store_units']) / store_frac if store_frac > 0 else float('inf'),
        float(EXECUTION_UNITS['fp_vec_units']) / fp_frac if fp_frac > 0 else float('inf'),
        float(cast(int, SOC_CONFIG['issue_width']))
    ]
    result = min(limits)
    return result


def compute_memory_stall_cpi(workload: Dict[str, Any], load_uops: float, instr_count: int) -> float:
    l1_miss = 1 - workload['l1d_hit_rate']
    l2_miss = 1 - workload['l2_hit_rate']
    l1_cycles = load_uops * workload['l1d_hit_rate'] * LATENCIES['l1d_hit']
    l2_cycles = load_uops * l1_miss * workload['l2_hit_rate'] * LATENCIES['l2_hit']
    mem_cycles = load_uops * l1_miss * l2_miss * LATENCIES['memory']
    result = (l1_cycles + l2_cycles + mem_cycles) / instr_count
    return result


def compute_backend_ipc(persona: str, uop_stats: Dict[str, Any], instr_count: int) -> Dict[str, Any]:
    workload = WORKLOADS[persona]
    resource_upc = compute_resource_limited_upc(uop_stats)
    mem_stall = compute_memory_stall_cpi(workload, uop_stats['load_uops'], instr_count)
    mispredicts = instr_count * workload['branch_fraction'] * workload['branch_mispredict_rate']
    branch_stall = mispredicts * LATENCIES['branch_mispredict'] / instr_count
    total_cpi = uop_stats['avg_uops_per_instr'] / resource_upc + mem_stall + branch_stall
    result = {
        'ipc_backend': 1.0 / total_cpi,
        'resource_limited_upc': resource_upc,
        'memory_stall_cpi': mem_stall,
        'branch_stall_cpi': branch_stall,
        'l1_miss_rate': 1 - workload['l1d_hit_rate'],
        'l2_miss_rate': 1 - workload['l2_hit_rate'],
        'branch_mispredicts': mispredicts
    }
    return result


def compute_trimode_backend_ipc(persona: str, uop_stats: Dict[str, Any], instr_count: int) -> Dict[str, Any]:
    workload = WORKLOADS[persona]
    resource_upc = compute_resource_limited_upc(uop_stats)
    mem_stall = compute_memory_stall_cpi(workload, uop_stats['load_uops'], instr_count)
    mispredicts = instr_count * workload['branch_fraction'] * workload['branch_mispredict_rate']
    mispredict_penalty = compute_trimode_mispredict_penalty(persona)
    branch_stall = mispredicts * mispredict_penalty / instr_count
    total_cpi = uop_stats['avg_uops_per_instr'] / resource_upc + mem_stall + branch_stall
    result = {
        'ipc_backend': 1.0 / total_cpi,
        'resource_limited_upc': resource_upc,
        'memory_stall_cpi': mem_stall,
        'branch_stall_cpi': branch_stall,
        'mispredict_penalty': mispredict_penalty
    }
    return result


def compute_native_uop_counts(persona: str, instr_count: int) -> Dict[str, Any]:
    result = compute_uop_counts_with_translation(WORKLOADS[persona], TRANSLATION_UOPS[persona], instr_count)
    return result


def compute_native_simulation(persona: str) -> Dict[str, Any]:
    uop_stats = compute_native_uop_counts(persona, INSTRUCTION_COUNT)
    frontend = compute_frontend_ipc(persona, uop_stats)
    backend = compute_backend_ipc(persona, uop_stats, INSTRUCTION_COUNT)

    ipc_frontend = frontend['ipc_frontend']
    ipc_backend = backend['ipc_backend']
    ipc_effective = min(ipc_frontend, ipc_backend)

    cycles = INSTRUCTION_COUNT / ipc_effective
    runtime_seconds = cycles / (cast(float, SOC_CONFIG['clock_ghz']) * 1e9)

    result = {
        'ipc': ipc_effective,
        'ipc_frontend': ipc_frontend,
        'ipc_backend': ipc_backend,
        'runtime_seconds': runtime_seconds,
        'total_uops': uop_stats['total_uops'],
        'avg_uops_per_instr': uop_stats['avg_uops_per_instr'],
        'memory_stall_cpi': backend['memory_stall_cpi'],
        'branch_stall_cpi': backend['branch_stall_cpi'],
        'cache_stats': {
            'l1_miss_rate': backend['l1_miss_rate'],
            'l2_miss_rate': backend['l2_miss_rate']
        }
    }
    return result


def compute_trimode_simulation(persona: str) -> Dict[str, Any]:
    workload = WORKLOADS[persona]
    adjusted_uop_stats = compute_adjusted_uop_stats(persona, INSTRUCTION_COUNT)
    frontend = compute_frontend_ipc(persona, adjusted_uop_stats)
    backend = compute_trimode_backend_ipc(persona, adjusted_uop_stats, INSTRUCTION_COUNT)

    ipc_raw = min(float(frontend['ipc_frontend']), float(backend['ipc_backend']))
    store_count = INSTRUCTION_COUNT * float(workload['store_fraction'])
    fence_stall_cycles = compute_fence_stall_cycles(persona, store_count)
    ipc_effective = compute_trimode_effective_ipc(ipc_raw, fence_stall_cycles, INSTRUCTION_COUNT)

    cycles = INSTRUCTION_COUNT / ipc_effective
    runtime_seconds = cycles / (cast(float, SOC_CONFIG['clock_ghz']) * 1e9)

    result = {
        'ipc': ipc_effective,
        'ipc_frontend': frontend['ipc_frontend'],
        'ipc_backend': backend['ipc_backend'],
        'runtime_seconds': runtime_seconds,
        'total_uops': adjusted_uop_stats['total_uops'],
        'avg_uops_per_instr': adjusted_uop_stats['avg_uops_per_instr']
    }
    return result


def json_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    result = {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET,POST,DELETE,OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type,x-api-key,x-test-mode'
        },
        'body': json.dumps(body)
    }
    return result


def error_response(status_code: int, error: str, details: str | None = None) -> Dict[str, Any]:
    body: Dict[str, Any] = {'success': False, 'error': error}
    if details:
        body['details'] = details
    result = json_response(status_code, body)
    return result


def verify_google_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify a Google ID token using Google's tokeninfo endpoint.

    Returns the token payload if valid, None if invalid.
    """
    if not GOOGLE_CLIENT_ID:
        return None

    try:
        url = f'https://oauth2.googleapis.com/tokeninfo?id_token={token}'
        req = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))

        # Verify the token was issued for our client
        if data.get('aud') != GOOGLE_CLIENT_ID:
            return None

        return data
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError):
        return None


def get_auth_token(event: Dict[str, Any]) -> Optional[str]:
    """Extract the Authorization token from the request headers."""
    headers = event.get('headers', {})
    if not headers:
        return None

    # Headers can be case-insensitive
    auth_header = headers.get('Authorization') or headers.get('authorization')
    if not auth_header:
        return None

    # Handle "Bearer <token>" format
    if auth_header.startswith('Bearer '):
        return auth_header[7:]

    return auth_header


def parse_body(event: Dict[str, Any]) -> Dict[str, Any]:
    body = event.get('body', {})
    result = json.loads(body) if isinstance(body, str) else body
    return result


def build_soc_config_output() -> Dict[str, Any]:
    result = {
        'clock_ghz': SOC_CONFIG['clock_ghz'],
        'ddr': f"{SOC_CONFIG['ddr_channels']}x {SOC_CONFIG['ddr_generation']}",
        'issue_width': SOC_CONFIG['issue_width'],
        'l1_size_kb': SOC_CONFIG['l1d_size_kb'],
        'l2_size_kb': SOC_CONFIG['l2_size_kb'],
        'process_nm': SOC_CONFIG['process_node_nm'],
        'rob_entries': SOC_CONFIG['rob_entries']
    }
    return result


def compute_simulation(persona: str) -> Dict[str, Any]:
    native_result = compute_native_simulation(persona)
    trimode_result = compute_trimode_simulation(persona)

    result = {
        'success': True,
        'persona': persona,
        'soc_config': build_soc_config_output(),
        'instruction_count': INSTRUCTION_COUNT,
        'native_core': {
            'description': 'Hypothetical single-core with equivalent microarchitecture for this ISA',
            'ipc': native_result['ipc'],
            'runtime_seconds': native_result['runtime_seconds'],
            'cache_stats': native_result['cache_stats'],
            'rob_ilp': math.sqrt(cast(int, SOC_CONFIG['rob_entries'])) * 0.6,
            'memory_stall_cpi': native_result['memory_stall_cpi'],
            'branch_stall_cpi': native_result['branch_stall_cpi']
        },
        'tri_mode_core': {
            'description': 'Tri-mode RISC-V core running this ISA via hardware translation',
            'ipc': trimode_result['ipc'],
            'runtime_seconds': trimode_result['runtime_seconds']
        },
        'relative_slowdown': trimode_result['runtime_seconds'] / native_result['runtime_seconds']
    }
    return result


def handle_simulation_soc_post(event: Dict[str, Any]) -> Dict[str, Any]:
    # Verify Google authentication
    token = get_auth_token(event)
    if not token:
        return error_response(401, 'Authentication required')

    user_info = verify_google_token(token)
    if not user_info:
        return error_response(401, 'Invalid or expired token')

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
        result = {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET,POST,DELETE,OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization,x-api-key,x-test-mode'
            },
            'body': ''
        }
    else:
        path = event.get('path', '')
        route_handler = ROUTE_MAP.get((path, method))
        if route_handler:
            result = route_handler(event)
        else:
            result = json_response(404, {'error': 'Not found'})
    return result
