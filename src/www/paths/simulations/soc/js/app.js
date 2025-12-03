var API_BASE_URL = 'https://api.10ulabs.com';

var socConfigLoaded = false;

var PERSONAS = ['riscv', 'x86_64', 'arm64'];
var PERSONA_LABELS = {
    'riscv': 'RISC-V',
    'x86_64': 'x86-64',
    'arm64': 'ARM64'
};

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

function formatPerformance(slowdown) {
    var percentChange = (1 - slowdown) * 100;
    return percentChange.toFixed(1) + '%';
}

function showResults(results) {
    var tbody = document.getElementById('resultsBody');
    var barChart = document.getElementById('barChart');
    tbody.innerHTML = '';
    barChart.innerHTML = '';

    var maxIpc = 0;
    results.forEach(function(data) {
        if (data.native_core.ipc > maxIpc) {
            maxIpc = data.native_core.ipc;
        }
        if (data.tri_mode_core.ipc > maxIpc) {
            maxIpc = data.tri_mode_core.ipc;
        }
    });

    results.forEach(function(data) {
        var row = document.createElement('tr');

        var isaCell = document.createElement('td');
        isaCell.textContent = PERSONA_LABELS[data.persona] || data.persona;
        row.appendChild(isaCell);

        var nativeCell = document.createElement('td');
        nativeCell.textContent = data.native_core.ipc.toFixed(3);
        row.appendChild(nativeCell);

        var multiIsaCell = document.createElement('td');
        multiIsaCell.textContent = data.tri_mode_core.ipc.toFixed(3);
        row.appendChild(multiIsaCell);

        var perfCell = document.createElement('td');
        perfCell.className = 'perf-negative';
        perfCell.textContent = formatPerformance(data.relative_slowdown);
        row.appendChild(perfCell);

        tbody.appendChild(row);

        var nativeBarRow = document.createElement('div');
        nativeBarRow.className = 'bar-row';
        nativeBarRow.innerHTML = '<span class="bar-label">' + (PERSONA_LABELS[data.persona] || data.persona) + ' Native</span>' +
            '<div class="bar-track"><div class="bar native-bar" style="width: ' + ((data.native_core.ipc / maxIpc) * 100) + '%"></div></div>' +
            '<span class="bar-value">' + data.native_core.ipc.toFixed(3) + '</span>';
        barChart.appendChild(nativeBarRow);

        var multiIsaBarRow = document.createElement('div');
        multiIsaBarRow.className = 'bar-row';
        multiIsaBarRow.innerHTML = '<span class="bar-label">' + (PERSONA_LABELS[data.persona] || data.persona) + ' Multi-ISA</span>' +
            '<div class="bar-track"><div class="bar alternate-bar" style="width: ' + ((data.tri_mode_core.ipc / maxIpc) * 100) + '%"></div></div>' +
            '<span class="bar-value">' + data.tri_mode_core.ipc.toFixed(3) + '</span>';
        barChart.appendChild(multiIsaBarRow);
    });

    document.getElementById('resultsPanel').style.display = 'block';
    document.getElementById('errorPanel').style.display = 'none';
}

function showError(message) {
    document.getElementById('errorMessage').textContent = message;
    document.getElementById('errorPanel').style.display = 'block';
    document.getElementById('resultsPanel').style.display = 'none';
}

function fetchSimulation(persona) {
    var baseUrl = getApiBaseUrl();
    return fetch(baseUrl + '/v1/simulation-soc', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ persona: persona })
    })
    .then(function(response) {
        return response.json();
    });
}

function loadAllSimulations() {
    var promises = PERSONAS.map(function(persona) {
        return fetchSimulation(persona);
    });

    Promise.all(promises)
        .then(function(results) {
            var successfulResults = results.filter(function(data) {
                return data.success;
            });

            if (successfulResults.length === 0) {
                showError('Failed to load simulations');
                return;
            }

            if (!socConfigLoaded && successfulResults.length > 0) {
                updateSocConfig(successfulResults[0].soc_config, successfulResults[0].instruction_count);
            }

            showResults(successfulResults);
        })
        .catch(function(error) {
            showError('Network error: ' + error.message);
        });
}

document.addEventListener('DOMContentLoaded', function() {
    loadAllSimulations();
});
