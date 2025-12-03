var API_BASE_URL = 'https://api.10ulabs.com';

var socConfigLoaded = false;

function getApiBaseUrl() {
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        return 'http://localhost:3000';
    }
    return API_BASE_URL;
}

function formatNumber(num) {
    if (num >= 1e9) {
        return (num / 1e9).toFixed(1) + 'B';
    }
    if (num >= 1e6) {
        return (num / 1e6).toFixed(1) + 'M';
    }
    if (num >= 1e3) {
        return (num / 1e3).toFixed(1) + 'K';
    }
    return num.toString();
}

function updateSocConfig(config, instructionCount) {
    document.getElementById('issueWidth').textContent = config.issue_width;
    document.getElementById('robEntries').textContent = config.rob_entries;
    document.getElementById('l1Size').textContent = config.l1_size_kb + ' KB';
    document.getElementById('l2Size').textContent = config.l2_size_kb + ' KB';
    document.getElementById('clockGhz').textContent = config.clock_ghz + ' GHz';
    document.getElementById('instructionCount').textContent = formatNumber(instructionCount);
    socConfigLoaded = true;
}

function showResults(data) {
    var personaLabels = {
        'riscv': 'RISC-V',
        'x86_64': 'x86-64',
        'arm64': 'ARM64'
    };

    document.getElementById('resultPersona').textContent = personaLabels[data.persona] || data.persona;

    document.getElementById('nativeIpc').textContent = data.native_core.ipc.toFixed(3);
    document.getElementById('nativeRuntime').textContent = data.native_core.runtime_seconds.toFixed(4);

    document.getElementById('multiIsaIpc').textContent = data.tri_mode_core.ipc.toFixed(3);
    document.getElementById('multiIsaRuntime').textContent = data.tri_mode_core.runtime_seconds.toFixed(4);

    document.getElementById('slowdownValue').textContent = data.relative_slowdown.toFixed(3) + 'x';

    var maxIpc = Math.max(data.native_core.ipc, data.tri_mode_core.ipc);
    var nativePercent = (data.native_core.ipc / maxIpc) * 100;
    var multiIsaPercent = (data.tri_mode_core.ipc / maxIpc) * 100;

    document.getElementById('nativeBar').style.width = nativePercent + '%';
    document.getElementById('nativeBarValue').textContent = data.native_core.ipc.toFixed(3);

    document.getElementById('multiIsaBar').style.width = multiIsaPercent + '%';
    document.getElementById('multiIsaBarValue').textContent = data.tri_mode_core.ipc.toFixed(3);

    document.getElementById('resultsPanel').style.display = 'block';
    document.getElementById('errorPanel').style.display = 'none';
}

function showError(message) {
    document.getElementById('errorMessage').textContent = message;
    document.getElementById('errorPanel').style.display = 'block';
    document.getElementById('resultsPanel').style.display = 'none';
}

function runSimulation() {
    var selectedPersona = document.querySelector('input[name="persona"]:checked');
    if (!selectedPersona) {
        showError('Please select a persona');
        return;
    }

    var persona = selectedPersona.value;
    var btn = document.getElementById('simulateBtn');
    btn.disabled = true;
    btn.textContent = 'Running...';

    var baseUrl = getApiBaseUrl();

    fetch(baseUrl + '/v1/simulation-soc', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ persona: persona })
    })
    .then(function(response) {
        return response.json();
    })
    .then(function(data) {
        btn.disabled = false;
        btn.textContent = 'Run Simulation';

        if (data.success) {
            if (!socConfigLoaded) {
                updateSocConfig(data.soc_config, data.instruction_count);
            }
            showResults(data);
        } else {
            showError(data.error || 'Simulation failed');
        }
    })
    .catch(function(error) {
        btn.disabled = false;
        btn.textContent = 'Run Simulation';
        showError('Network error: ' + error.message);
    });
}

function loadInitialConfig() {
    var baseUrl = getApiBaseUrl();

    fetch(baseUrl + '/v1/simulation-soc', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ persona: 'riscv' })
    })
    .then(function(response) {
        return response.json();
    })
    .then(function(data) {
        if (data.success) {
            updateSocConfig(data.soc_config, data.instruction_count);
        }
    })
    .catch(function() {
    });
}

document.addEventListener('DOMContentLoaded', function() {
    loadInitialConfig();
});
