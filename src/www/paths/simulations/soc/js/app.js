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
    document.getElementById('instructionCount').textContent = formatNumber(instructionCount);
    socConfigLoaded = true;
}

var socClockGhz = null;

function formatPerformance(slowdown) {
    var percentChange = (1 - slowdown) * 100;
    return percentChange.toFixed(1) + '%';
}

function createSocCard(label, ipc, maxIpc, cardType, perfText, subtitle) {
    var card = document.createElement('div');
    card.className = 'soc-card ' + cardType;

    var title = document.createElement('div');
    title.className = 'soc-card-title';
    title.textContent = label;
    card.appendChild(title);

    if (subtitle) {
        var subtitleEl = document.createElement('div');
        subtitleEl.className = 'soc-card-subtitle';
        subtitleEl.textContent = subtitle;
        card.appendChild(subtitleEl);
    }

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
        var isPositive = perfText.charAt(0) !== '-';
        perf.className = 'soc-card-perf ' + (isPositive ? 'positive' : 'negative');
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

    if (results.length > 0) {
        socClockGhz = results[0].soc_config.clock_ghz;
    }

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
    nativeLabel.textContent = 'Non-Tri-Mode Core';
    socGrid.appendChild(nativeLabel);

    PERSONAS.forEach(function(persona) {
        var data = resultsByPersona[persona];
        if (data) {
            var label = PERSONA_LABELS[persona] || persona;
            var subtitle = socClockGhz + ' GHz';
            var card = createSocCard(label, data.native_core.ipc, maxIpc, 'native', null, subtitle);
            socGrid.appendChild(card);
        }
    });

    var triModeLabel = document.createElement('div');
    triModeLabel.className = 'soc-row-label';
    triModeLabel.textContent = 'Tri-Mode Core';
    socGrid.appendChild(triModeLabel);

    PERSONAS.forEach(function(persona) {
        var data = resultsByPersona[persona];
        if (data) {
            var label = PERSONA_LABELS[persona] || persona;
            var perfText = formatPerformance(data.relative_slowdown);
            var subtitle = socClockGhz + ' GHz';
            var card = createSocCard(label, data.tri_mode_core.ipc, maxIpc, 'tri-mode', perfText, subtitle);
            socGrid.appendChild(card);
        }
    });

    document.getElementById('resultsPanel').style.display = 'block';
    document.getElementById('errorPanel').style.display = 'none';

    showRealWorldResults(results, resultsByPersona);
}

function showRealWorldResults(results, resultsByPersona) {
    var realWorldGrid = document.getElementById('realWorldGrid');
    realWorldGrid.innerHTML = '';

    var maxIpc = 0;
    results.forEach(function(data) {
        var rw = data.real_world_comparison;
        if (rw) {
            if (rw.native_core.ipc > maxIpc) {
                maxIpc = rw.native_core.ipc;
            }
            if (rw.tri_mode_core.ipc > maxIpc) {
                maxIpc = rw.tri_mode_core.ipc;
            }
        }
    });

    var nativeLabel = document.createElement('div');
    nativeLabel.className = 'soc-row-label';
    nativeLabel.textContent = 'Native Core';
    realWorldGrid.appendChild(nativeLabel);

    PERSONAS.forEach(function(persona) {
        var data = resultsByPersona[persona];
        if (data && data.real_world_comparison) {
            var rw = data.real_world_comparison;
            var label = PERSONA_LABELS[persona] || persona;
            var subtitle = rw.native_core.name + ' @ ' + rw.clock_ghz + ' GHz';
            var card = createSocCard(label, rw.native_core.ipc, maxIpc, 'native', null, subtitle);
            realWorldGrid.appendChild(card);
        }
    });

    var triModeLabel = document.createElement('div');
    triModeLabel.className = 'soc-row-label';
    triModeLabel.textContent = 'Tri-Mode Core';
    realWorldGrid.appendChild(triModeLabel);

    PERSONAS.forEach(function(persona) {
        var data = resultsByPersona[persona];
        if (data && data.real_world_comparison) {
            var rw = data.real_world_comparison;
            var label = PERSONA_LABELS[persona] || persona;
            var perfText = formatPerformance(rw.relative_slowdown);
            var subtitle = 'Same clock as native';
            var card = createSocCard(label, rw.tri_mode_core.ipc, maxIpc, 'tri-mode', perfText, subtitle);
            realWorldGrid.appendChild(card);
        }
    });

    document.getElementById('realWorldPanel').style.display = 'block';
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
