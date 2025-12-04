import json
import math
from typing import Any, Dict, cast

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
    'clock_ghz': 3.0,
    'pipeline_depth_estimate': 18
}

REAL_WORLD_CORES = {
    'x86_64': {
        'name': 'Pentium 4 Prescott',
        'issue_width': 3,
        'rob_entries': 126,
        'l1d_size_kb': 16,
        'l2_size_kb': 1024,
        'clock_ghz': 3.4,
        'int_alus': 3,
        'load_units': 2,
        'store_units': 1,
        'fp_vec_units': 2
    },
    'arm64': {
        'name': 'Cortex-A57',
        'issue_width': 3,
        'rob_entries': 128,
        'l1d_size_kb': 32,
        'l2_size_kb': 2048,
        'clock_ghz': 2.0,
        'int_alus': 2,
        'load_units': 1,
        'store_units': 1,
        'fp_vec_units': 2
    },
    'riscv': {
        'name': 'SiFive U74',
        'issue_width': 2,
        'rob_entries': 64,
        'l1d_size_kb': 32,
        'l2_size_kb': 2048,
        'clock_ghz': 1.5,
        'int_alus': 2,
        'load_units': 1,
        'store_units': 1,
        'fp_vec_units': 1
    }
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

TRIMODE_DECODE_OVERHEAD = {
    'riscv': 0.02,
    'x86_64': 0.05,
    'arm64': 0.03,
}

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


def compute_frontend_ipc(persona: str, uop_stats: Dict[str, Any], trimode: bool = False) -> Dict[str, Any]:
    workload = WORKLOADS[persona]
    fetch_bytes_per_cycle = 16.0
    issue_width = float(SOC_CONFIG['issue_width'])
    avg_bytes = workload['avg_bytes_per_instr']
    avg_uops = uop_stats['avg_uops_per_instr']
    fetch_limited = fetch_bytes_per_cycle / avg_bytes
    decode_overhead = TRIMODE_DECODE_OVERHEAD[persona] if trimode else 0.0
    decode_efficiency = 1.0 - decode_overhead
    decode_limited = issue_width * decode_efficiency
    uop_limited = issue_width / avg_uops
    ipc_frontend = min(fetch_limited, decode_limited, uop_limited)
    result = {
        'ipc_frontend': ipc_frontend,
        'fetch_limited_ipc': fetch_limited,
        'decode_limited_ipc': decode_limited,
        'uop_emission_limited_ipc': uop_limited
    }
    return result


def compute_frontend_ipc_with_config(persona: str, uop_stats: Dict[str, Any],
                                     core_config: Dict[str, Any]) -> Dict[str, Any]:
    workload = WORKLOADS[persona]
    fetch_bytes_per_cycle = 16.0
    issue_width = float(core_config['issue_width'])
    avg_bytes = workload['avg_bytes_per_instr']
    avg_uops = uop_stats['avg_uops_per_instr']
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


def compute_resource_limited_upc_with_config(uop_stats: Dict[str, Any], core_config: Dict[str, Any]) -> float:
    total = uop_stats['total_uops']
    alu_frac = (uop_stats['alu_uops'] + uop_stats['branch_uops'] + uop_stats['complex_uops'] * 0.5) / total
    load_frac = uop_stats['load_uops'] / total
    store_frac = uop_stats['store_uops'] / total
    fp_frac = (uop_stats['fp_vec_uops'] + uop_stats['complex_uops'] * 0.5) / total
    limits = [
        core_config['int_alus'] / alu_frac if alu_frac > 0 else float('inf'),
        core_config['load_units'] / load_frac if load_frac > 0 else float('inf'),
        core_config['store_units'] / store_frac if store_frac > 0 else float('inf'),
        core_config['fp_vec_units'] / fp_frac if fp_frac > 0 else float('inf'),
        core_config['issue_width']
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


def compute_backend_ipc_with_config(persona: str, uop_stats: Dict[str, Any], instr_count: int,
                                    core_config: Dict[str, Any]) -> Dict[str, Any]:
    workload = WORKLOADS[persona]
    resource_upc = compute_resource_limited_upc_with_config(uop_stats, core_config)
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
    result = compute_uop_counts_with_translation(WORKLOADS[persona], TRANSLATION_UOPS[persona], instr_count)
    return result


def compute_native_simulation(persona: str) -> Dict[str, Any]:
    uop_stats = compute_native_uop_counts(persona, INSTRUCTION_COUNT)
    frontend = compute_frontend_ipc(persona, uop_stats, trimode=False)
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
    uop_stats = compute_uop_counts(persona, INSTRUCTION_COUNT)
    frontend = compute_frontend_ipc(persona, uop_stats, trimode=True)
    backend = compute_backend_ipc(persona, uop_stats, INSTRUCTION_COUNT)

    ipc_frontend = frontend['ipc_frontend']
    ipc_backend = backend['ipc_backend']
    ipc_raw = min(ipc_frontend, ipc_backend)

    decode_overhead = TRIMODE_DECODE_OVERHEAD[persona]
    ipc_effective = ipc_raw * (1.0 - decode_overhead)

    cycles = INSTRUCTION_COUNT / ipc_effective
    runtime_seconds = cycles / (SOC_CONFIG['clock_ghz'] * 1e9)

    result = {
        'ipc': ipc_effective,
        'ipc_frontend': ipc_frontend,
        'ipc_backend': ipc_backend,
        'runtime_seconds': runtime_seconds,
        'total_uops': uop_stats['total_uops'],
        'avg_uops_per_instr': uop_stats['avg_uops_per_instr']
    }
    return result


def compute_real_world_simulation(persona: str) -> Dict[str, Any]:
    core_config = REAL_WORLD_CORES[persona]
    uop_stats = compute_uop_counts(persona, INSTRUCTION_COUNT)
    frontend = compute_frontend_ipc_with_config(persona, uop_stats, core_config)
    backend = compute_backend_ipc_with_config(persona, uop_stats, INSTRUCTION_COUNT, core_config)

    ipc_frontend = frontend['ipc_frontend']
    ipc_backend = backend['ipc_backend']
    ipc_effective = min(ipc_frontend, ipc_backend)

    cycles = INSTRUCTION_COUNT / ipc_effective
    clock_ghz = cast(float, core_config['clock_ghz'])
    runtime_seconds = cycles / (clock_ghz * 1e9)

    result = {
        'core_name': core_config['name'],
        'ipc': ipc_effective,
        'ipc_frontend': ipc_frontend,
        'ipc_backend': ipc_backend,
        'runtime_seconds': runtime_seconds,
        'clock_ghz': core_config['clock_ghz'],
        'total_uops': uop_stats['total_uops'],
        'avg_uops_per_instr': uop_stats['avg_uops_per_instr'],
        'memory_stall_cpi': backend['memory_stall_cpi'],
        'branch_stall_cpi': backend['branch_stall_cpi']
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


def build_soc_config_output() -> Dict[str, Any]:
    result = {
        'issue_width': SOC_CONFIG['issue_width'],
        'rob_entries': SOC_CONFIG['rob_entries'],
        'l1_size_kb': SOC_CONFIG['l1d_size_kb'],
        'l2_size_kb': SOC_CONFIG['l2_size_kb'],
        'clock_ghz': SOC_CONFIG['clock_ghz']
    }
    return result


def build_real_world_config(persona: str) -> Dict[str, Any]:
    core = REAL_WORLD_CORES[persona]
    result = {
        'name': core['name'],
        'issue_width': core['issue_width'],
        'rob_entries': core['rob_entries'],
        'l1_size_kb': core['l1d_size_kb'],
        'l2_size_kb': core['l2_size_kb'],
        'clock_ghz': core['clock_ghz']
    }
    return result


def compute_simulation(persona: str) -> Dict[str, Any]:
    native_result = compute_native_simulation(persona)
    trimode_result = compute_trimode_simulation(persona)
    real_world_result = compute_real_world_simulation(persona)
    real_world_clock = cast(float, REAL_WORLD_CORES[persona]['clock_ghz'])

    trimode_runtime_at_real_clock = (INSTRUCTION_COUNT / trimode_result['ipc']) / (real_world_clock * 1e9)

    result = {
        'success': True,
        'persona': persona,
        'soc_config': build_soc_config_output(),
        'instruction_count': INSTRUCTION_COUNT,
        'native_core': {
            'description': 'Hypothetical P4-class core with equivalent microarchitecture for this ISA',
            'ipc': native_result['ipc'],
            'runtime_seconds': native_result['runtime_seconds'],
            'cache_stats': native_result['cache_stats'],
            'rob_ilp': math.sqrt(SOC_CONFIG['rob_entries']) * 0.6,
            'memory_stall_cpi': native_result['memory_stall_cpi'],
            'branch_stall_cpi': native_result['branch_stall_cpi']
        },
        'tri_mode_core': {
            'description': 'Tri-mode RISC-V core running this ISA via hardware translation',
            'ipc': trimode_result['ipc'],
            'runtime_seconds': trimode_result['runtime_seconds']
        },
        'relative_slowdown': trimode_result['runtime_seconds'] / native_result['runtime_seconds'],
        'real_world_comparison': {
            'description': 'Comparison at same clock speed against actual commercial processors',
            'clock_ghz': real_world_clock,
            'native_core': {
                'name': real_world_result['core_name'],
                'config': build_real_world_config(persona),
                'ipc': real_world_result['ipc'],
                'runtime_seconds': real_world_result['runtime_seconds'],
                'memory_stall_cpi': real_world_result['memory_stall_cpi'],
                'branch_stall_cpi': real_world_result['branch_stall_cpi']
            },
            'tri_mode_core': {
                'description': 'Tri-mode core at same clock as native',
                'ipc': trimode_result['ipc'],
                'runtime_seconds': trimode_runtime_at_real_clock
            },
            'relative_slowdown': trimode_runtime_at_real_clock / real_world_result['runtime_seconds']
        }
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
