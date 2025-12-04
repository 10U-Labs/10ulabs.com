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

function updateSocConfig(config) {
    document.getElementById('clockSpeed').textContent = config.clock_ghz + ' GHz';
    document.getElementById('ddr').textContent = config.ddr;
    document.getElementById('issueWidth').textContent = config.issue_width;
    document.getElementById('l1Size').textContent = config.l1_size_kb + ' KB';
    document.getElementById('l2Size').textContent = config.l2_size_kb + ' KB';
    document.getElementById('processNode').textContent = config.process_nm + ' nm';
    document.getElementById('robEntries').textContent = config.rob_entries;
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
        var isPositive = perfText.charAt(0) !== '-';
        perf.className = 'soc-card-perf ' + (isPositive ? 'positive' : 'negative');
        perf.textContent = perfText;
        card.appendChild(perf);
    }

    return card;
}

function createCoreDiagramSvg(activeIsa) {
    var svgNS = 'http://www.w3.org/2000/svg';
    var svg = document.createElementNS(svgNS, 'svg');
    svg.setAttribute('viewBox', '0 0 220 320');
    svg.setAttribute('class', 'core-diagram');

    function rect(x, y, w, h, classes) {
        var r = document.createElementNS(svgNS, 'rect');
        r.setAttribute('x', x);
        r.setAttribute('y', y);
        r.setAttribute('width', w);
        r.setAttribute('height', h);
        r.setAttribute('rx', '4');
        r.setAttribute('class', classes);
        return r;
    }

    function text(x, y, content, classes) {
        var t = document.createElementNS(svgNS, 'text');
        t.setAttribute('x', x);
        t.setAttribute('y', y);
        t.setAttribute('class', classes);
        t.textContent = content;
        return t;
    }

    function path(d, classes) {
        var p = document.createElementNS(svgNS, 'path');
        p.setAttribute('d', d);
        p.setAttribute('class', classes);
        return p;
    }

    var isTriMode = activeIsa !== 'native';
    var arm64Active = activeIsa === 'arm64';
    var riscvActive = activeIsa === 'riscv' || activeIsa === 'native';
    var x86Active = activeIsa === 'x86_64';

    // Instruction Fetch + Mode Steering
    svg.appendChild(rect(10, 10, 200, 25, 'block active'));
    svg.appendChild(text(110, 27, 'Instruction Fetch', 'block-text'));

    if (isTriMode) {
        // Mode steering
        svg.appendChild(rect(10, 45, 200, 18, 'block active mode-steer'));
        svg.appendChild(text(110, 57, 'Mode Steering (ISA bits)', 'block-text tiny'));
        svg.appendChild(path('M110 35 L110 45', 'arrow active'));

        // Three parallel decode lanes
        svg.appendChild(rect(10, 73, 60, 22, 'block ' + (arm64Active ? 'active arm64' : 'inactive')));
        svg.appendChild(text(40, 88, 'ARM64', 'block-text small' + (arm64Active ? '' : ' inactive')));

        svg.appendChild(rect(80, 73, 60, 22, 'block ' + (riscvActive ? 'active riscv' : 'inactive')));
        svg.appendChild(text(110, 88, 'RISC-V', 'block-text small' + (riscvActive ? '' : ' inactive')));

        svg.appendChild(rect(150, 73, 60, 22, 'block ' + (x86Active ? 'active x86' : 'inactive')));
        svg.appendChild(text(180, 88, 'x86-64', 'block-text small' + (x86Active ? '' : ' inactive')));

        // Arrows to decode lanes
        svg.appendChild(path('M40 63 L40 73', 'arrow ' + (arm64Active ? 'active' : 'inactive')));
        svg.appendChild(path('M110 63 L110 73', 'arrow ' + (riscvActive ? 'active' : 'inactive')));
        svg.appendChild(path('M180 63 L180 73', 'arrow ' + (x86Active ? 'active' : 'inactive')));

        // Micro-op queue (all lanes emit here)
        svg.appendChild(rect(10, 105, 200, 22, 'block active'));
        svg.appendChild(text(110, 120, 'Micro-op Queue (RISC-V ops)', 'block-text tiny'));

        // Arrows from decoders to micro-op queue
        svg.appendChild(path('M40 95 L40 105', 'arrow ' + (arm64Active ? 'active' : 'inactive')));
        svg.appendChild(path('M110 95 L110 105', 'arrow ' + (riscvActive ? 'active' : 'inactive')));
        svg.appendChild(path('M180 95 L180 105', 'arrow ' + (x86Active ? 'active' : 'inactive')));

        // Flags predictor (side component for x86/ARM)
        if (x86Active || arm64Active) {
            svg.appendChild(rect(165, 137, 45, 35, 'block active optimization'));
            svg.appendChild(text(187, 152, 'Flags', 'block-text tiny'));
            svg.appendChild(text(187, 163, 'Predictor', 'block-text tiny'));
        }

        svg.appendChild(path('M110 127 L110 137', 'arrow active'));
    } else {
        // Non-tri-mode: single RISC-V decoder
        svg.appendChild(path('M110 35 L110 73', 'arrow active'));
        svg.appendChild(rect(50, 73, 120, 22, 'block active'));
        svg.appendChild(text(110, 88, 'RISC-V Decoder', 'block-text small'));
        svg.appendChild(path('M110 95 L110 137', 'arrow active'));
    }

    // Rename/Dispatch
    svg.appendChild(rect(10, 137, 145, 22, 'block active'));
    svg.appendChild(text(82, 152, 'Rename / Dispatch', 'block-text small'));
    svg.appendChild(path('M110 159 L110 172', 'arrow active'));

    // ROB + Register File
    svg.appendChild(rect(10, 172, 95, 22, 'block active'));
    svg.appendChild(text(57, 187, 'ROB (128)', 'block-text small'));
    svg.appendChild(rect(115, 172, 95, 22, 'block active'));
    svg.appendChild(text(162, 187, 'Registers', 'block-text small'));
    svg.appendChild(path('M110 194 L110 207', 'arrow active'));

    // Execution Units
    svg.appendChild(rect(10, 207, 200, 22, 'block active'));
    svg.appendChild(text(110, 222, 'Execution Units (3-wide)', 'block-text small'));
    svg.appendChild(path('M110 229 L110 242', 'arrow active'));

    // Load-Store Unit with TSO mode
    if (isTriMode && x86Active) {
        svg.appendChild(rect(10, 242, 200, 22, 'block active optimization'));
        svg.appendChild(text(110, 257, 'Load-Store Unit [TSO mode]', 'block-text small'));
    } else {
        svg.appendChild(rect(10, 242, 200, 22, 'block active'));
        svg.appendChild(text(110, 257, 'Load-Store Unit', 'block-text small'));
    }
    svg.appendChild(path('M110 264 L110 277', 'arrow active'));

    // L1 Cache
    svg.appendChild(rect(10, 277, 95, 18, 'block active'));
    svg.appendChild(text(57, 290, 'L1I 32KB', 'block-text tiny'));
    svg.appendChild(rect(115, 277, 95, 18, 'block active'));
    svg.appendChild(text(162, 290, 'L1D 32KB', 'block-text tiny'));
    svg.appendChild(path('M110 295 L110 305', 'arrow active'));

    // L2 Cache
    svg.appendChild(rect(10, 305, 200, 15, 'block active'));
    svg.appendChild(text(110, 316, 'L2 512KB', 'block-text tiny'));

    return svg;
}

function createDiagramCard(title, badgeClass, badgeText, activeIsa) {
    var card = document.createElement('div');
    card.className = 'diagram-card';

    var titleDiv = document.createElement('div');
    titleDiv.className = 'diagram-title';
    titleDiv.textContent = title + ' ';

    if (badgeText) {
        var badge = document.createElement('span');
        badge.className = 'isa-badge ' + badgeClass;
        badge.textContent = badgeText;
        titleDiv.appendChild(badge);
    }

    card.appendChild(titleDiv);
    card.appendChild(createCoreDiagramSvg(activeIsa));

    return card;
}

function createNonTriModeDiagram() {
    var container = document.createElement('div');
    container.className = 'diagram-row diagram-row-single';
    container.appendChild(createDiagramCard('Non-Tri-Mode Core', '', '', 'native'));
    return container;
}

function createTriModeDiagrams() {
    var container = document.createElement('div');
    container.className = 'diagram-row diagram-row-triple';
    container.appendChild(createDiagramCard('Tri-Mode Core', 'arm64', 'ARM64', 'arm64'));
    container.appendChild(createDiagramCard('Tri-Mode Core', 'riscv', 'RISC-V', 'riscv'));
    container.appendChild(createDiagramCard('Tri-Mode Core', 'x86', 'x86-64', 'x86_64'));
    return container;
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

    // Non-Tri-Mode section
    var nativeLabel = document.createElement('div');
    nativeLabel.className = 'soc-row-label';
    nativeLabel.textContent = 'Non-Tri-Mode Core';
    socGrid.appendChild(nativeLabel);

    PERSONAS.forEach(function(persona) {
        var data = resultsByPersona[persona];
        if (data) {
            var label = PERSONA_LABELS[persona] || persona;
            var card = createSocCard(label, data.native_core.ipc, maxIpc, 'native', null);
            socGrid.appendChild(card);
        }
    });

    // Non-Tri-Mode diagram
    socGrid.appendChild(createNonTriModeDiagram());

    // Tri-Mode section
    var triModeLabel = document.createElement('div');
    triModeLabel.className = 'soc-row-label';
    triModeLabel.textContent = 'Tri-Mode Core';
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

    // Tri-Mode diagrams
    socGrid.appendChild(createTriModeDiagrams());

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
    var headers = {
        'Content-Type': 'application/json'
    };

    // Add Authorization header if authenticated
    var token = typeof getAccessToken === 'function' ? getAccessToken() : null;
    if (token) {
        headers['Authorization'] = token;
    }

    return fetch(baseUrl + '/v1/simulation-soc', {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({ persona: persona })
    })
    .then(function(response) {
        if (response.status === 401) {
            // Token expired or invalid, clear auth and reload
            if (typeof clearStoredAuth === 'function') {
                clearStoredAuth();
            }
            window.location.reload();
            throw new Error('Authentication required');
        }
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
                updateSocConfig(successfulResults[0].soc_config);
            }

            showResults(successfulResults);
        })
        .catch(function(error) {
            showError('Network error: ' + error.message);
        });
}

// Note: loadAllSimulations is called by auth.js after successful authentication
