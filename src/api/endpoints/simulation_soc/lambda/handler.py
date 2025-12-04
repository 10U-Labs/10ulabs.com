import json
import math
from typing import Any, Dict

SOC_CONFIG = {
    'issue_width': 4,
    'backend_dispatch_width': 4,
    'rob_entries': 128,
    'int_phys_regs': 192,
    'fp_vec_phys_regs': 160,
    'load_queue_entries': 64,
    'store_queue_entries': 64,
    'l1i_size_kb': 32,
    'l1d_size_kb': 32,
    'l2_size_kb': 512,
    'clock_ghz': 3.0,
    'pipeline_depth_estimate': 18
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

SPEC_TRANSLATION_RANGES = {
    'riscv': {
        'alu': (1, 1),
        'load': (1, 1),
        'store': (1, 1),
        'branch': (1, 1),
        'fp_vec': (1, 1),
        'complex': (2, 2),
    },
    'x86_64': {
        'alu': (1, 2),
        'load': (2, 3),
        'store': (2, 3),
        'branch': (1, 2),
        'fp_vec': (2, 4),
        'complex': (8, 32),
    },
    'arm64': {
        'alu': (1, 2),
        'load': (1, 3),
        'store': (1, 3),
        'branch': (1, 2),
        'fp_vec': (1, 4),
        'complex': (1, 4),
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
    max_decode_per_cycle = 4.0
    max_uops_per_cycle = 4.0

    avg_bytes = workload['avg_bytes_per_instr']
    avg_uops = uop_stats['avg_uops_per_instr']

    fetch_limited_ipc = fetch_bytes_per_cycle / avg_bytes
    decode_limited_ipc = max_decode_per_cycle
    uop_emission_limited_ipc = max_uops_per_cycle / avg_uops

    ipc_frontend = min(fetch_limited_ipc, decode_limited_ipc, uop_emission_limited_ipc)

    result = {
        'ipc_frontend': ipc_frontend,
        'fetch_limited_ipc': fetch_limited_ipc,
        'decode_limited_ipc': decode_limited_ipc,
        'uop_emission_limited_ipc': uop_emission_limited_ipc
    }
    return result


def compute_resource_limited_upc(uop_stats: Dict[str, Any]) -> float:
    total = uop_stats['total_uops']
    alu_frac = (uop_stats['alu_uops'] + uop_stats['branch_uops'] + uop_stats['complex_uops'] * 0.5) / total
    load_frac = uop_stats['load_uops'] / total
    store_frac = uop_stats['store_uops'] / total
    fp_frac = (uop_stats['fp_vec_uops'] + uop_stats['complex_uops'] * 0.5) / total
    limits = [
        EXECUTION_UNITS['int_alus'] / alu_frac if alu_frac > 0 else float('inf'),
        EXECUTION_UNITS['load_units'] / load_frac if load_frac > 0 else float('inf'),
        EXECUTION_UNITS['store_units'] / store_frac if store_frac > 0 else float('inf'),
        EXECUTION_UNITS['fp_vec_units'] / fp_frac if fp_frac > 0 else float('inf'),
        SOC_CONFIG['issue_width']
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


def compute_native_uop_counts(persona: str, instr_count: int) -> Dict[str, Any]:
    result = compute_uop_counts_with_translation(WORKLOADS[persona], TRANSLATION_UOPS['riscv'], instr_count)
    return result


def compute_native_simulation(persona: str) -> Dict[str, Any]:
    uop_stats = compute_native_uop_counts(persona, INSTRUCTION_COUNT)
    frontend = compute_frontend_ipc(persona, uop_stats)
    backend = compute_backend_ipc(persona, uop_stats, INSTRUCTION_COUNT)

    ipc_frontend = frontend['ipc_frontend']
    ipc_backend = backend['ipc_backend']
    ipc_effective = min(ipc_frontend, ipc_backend)

    cycles = INSTRUCTION_COUNT / ipc_effective
    runtime_seconds = cycles / (SOC_CONFIG['clock_ghz'] * 1e9)

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
    native_riscv = compute_native_simulation('riscv')
    riscv_ipc = native_riscv['ipc']

    uop_stats = compute_uop_counts(persona, INSTRUCTION_COUNT)
    frontend = compute_frontend_ipc(persona, uop_stats)
    backend = compute_backend_ipc(persona, uop_stats, INSTRUCTION_COUNT)

    ipc_frontend = frontend['ipc_frontend']
    ipc_backend = backend['ipc_backend']
    ipc_effective = min(ipc_frontend, ipc_backend)

    cycles = INSTRUCTION_COUNT / ipc_effective
    runtime_seconds = cycles / (SOC_CONFIG['clock_ghz'] * 1e9)

    overhead_factor = ipc_effective / riscv_ipc if riscv_ipc > 0 else 0

    result = {
        'ipc': ipc_effective,
        'ipc_frontend': ipc_frontend,
        'ipc_backend': ipc_backend,
        'runtime_seconds': runtime_seconds,
        'overhead_factor': overhead_factor,
        'total_uops': uop_stats['total_uops'],
        'avg_uops_per_instr': uop_stats['avg_uops_per_instr']
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


def parse_body(event: Dict[str, Any]) -> Dict[str, Any]:
    body = event.get('body', {})
    result = json.loads(body) if isinstance(body, str) else body
    return result


def compute_simulation(persona: str) -> Dict[str, Any]:
    native_result = compute_native_simulation(persona)
    trimode_result = compute_trimode_simulation(persona)

    native_ipc = native_result['ipc']
    trimode_ipc = trimode_result['ipc']

    native_runtime = native_result['runtime_seconds']
    trimode_runtime = trimode_result['runtime_seconds']

    relative_slowdown = trimode_runtime / native_runtime if native_runtime > 0 else 1.0

    soc_config_output = {
        'issue_width': SOC_CONFIG['issue_width'],
        'rob_entries': SOC_CONFIG['rob_entries'],
        'l1_size_kb': SOC_CONFIG['l1d_size_kb'],
        'l2_size_kb': SOC_CONFIG['l2_size_kb'],
        'clock_ghz': SOC_CONFIG['clock_ghz']
    }

    result = {
        'success': True,
        'persona': persona,
        'soc_config': soc_config_output,
        'instruction_count': INSTRUCTION_COUNT,
        'native_core': {
            'ipc': native_ipc,
            'runtime_seconds': native_runtime,
            'cache_stats': native_result['cache_stats'],
            'rob_ilp': math.sqrt(SOC_CONFIG['rob_entries']) * 0.6,
            'memory_stall_cpi': native_result['memory_stall_cpi'],
            'branch_stall_cpi': native_result['branch_stall_cpi']
        },
        'tri_mode_core': {
            'ipc': trimode_ipc,
            'runtime_seconds': trimode_runtime,
            'overhead_factor': trimode_result['overhead_factor']
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
        result = {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET,POST,DELETE,OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type,x-api-key,x-test-mode'
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
