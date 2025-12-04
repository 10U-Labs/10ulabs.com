var API_BASE_URL = 'https://api.10ulabs.com';

var socConfigLoaded = false;

var PERSONAS = ['arm64', 'riscv', 'x86_64'];
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

function createSocCard(label, ipc, maxIpc, cardType, perfText) {
    var card = document.createElement('div');
    card.className = 'soc-card ' + cardType;

    var title = document.createElement('div');
    title.className = 'soc-card-title';
    title.textContent = label;
    card.appendChild(title);

    var ipcValue = document.createElement('div');
    ipcValue.className = 'soc-card-ipc';
    ipcValue.textContent = ipc.toFixed(3);
    card.appendChild(ipcValue);

    var ipcLabel = document.createElement('div');
    ipcLabel.className = 'soc-card-ipc-label';
    ipcLabel.textContent = 'IPC';
    card.appendChild(ipcLabel);

    var bar = document.createElement('div');
    bar.className = 'soc-card-bar';
    var barFill = document.createElement('div');
    barFill.className = 'soc-card-bar-fill';
    barFill.style.width = ((ipc / maxIpc) * 100) + '%';
    bar.appendChild(barFill);
    card.appendChild(bar);

    if (perfText) {
        var perf = document.createElement('div');
        perf.className = 'soc-card-perf negative';
        perf.textContent = perfText;
        card.appendChild(perf);
    }

    return card;
}

function showResults(results) {
    var socGrid = document.getElementById('socGrid');
    socGrid.innerHTML = '';

    var resultsByPersona = {};
    results.forEach(function(data) {
        resultsByPersona[data.persona] = data;
    });

    var maxIpc = 0;
    results.forEach(function(data) {
        if (data.native_core.ipc > maxIpc) {
            maxIpc = data.native_core.ipc;
        }
        if (data.tri_mode_core.ipc > maxIpc) {
            maxIpc = data.tri_mode_core.ipc;
        }
    });

    var nativeLabel = document.createElement('div');
    nativeLabel.className = 'soc-row-label';
    nativeLabel.textContent = 'Native Cores';
    socGrid.appendChild(nativeLabel);

    PERSONAS.forEach(function(persona) {
        var data = resultsByPersona[persona];
        if (data) {
            var label = PERSONA_LABELS[persona] || persona;
            var card = createSocCard(label, data.native_core.ipc, maxIpc, 'native', null);
            socGrid.appendChild(card);
        }
    });

    var triModeLabel = document.createElement('div');
    triModeLabel.className = 'soc-row-label';
    triModeLabel.textContent = 'Tri-Mode Cores';
    socGrid.appendChild(triModeLabel);

    PERSONAS.forEach(function(persona) {
        var data = resultsByPersona[persona];
        if (data) {
            var label = PERSONA_LABELS[persona] || persona;
            var perfText = formatPerformance(data.relative_slowdown);
            var card = createSocCard(label, data.tri_mode_core.ipc, maxIpc, 'tri-mode', perfText);
            socGrid.appendChild(card);
        }
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
