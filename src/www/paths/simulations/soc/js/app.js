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
    svg.setAttribute('viewBox', '0 0 200 240');
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

    // Instruction Fetch
    svg.appendChild(rect(10, 10, 180, 30, 'block active'));
    svg.appendChild(text(100, 30, 'Instruction Fetch', 'block-text'));

    if (activeIsa === 'native') {
        // Single decoder for native
        svg.appendChild(rect(60, 55, 80, 25, 'block active'));
        svg.appendChild(text(100, 72, 'Decoder', 'block-text small'));
        svg.appendChild(path('M100 40 L100 55', 'arrow active'));
        svg.appendChild(path('M100 80 L100 95', 'arrow active'));
    } else {
        // Three decoders for tri-mode
        var arm64Active = activeIsa === 'arm64';
        var riscvActive = activeIsa === 'riscv';
        var x86Active = activeIsa === 'x86_64';

        svg.appendChild(rect(10, 55, 55, 25, 'block ' + (arm64Active ? 'active arm64' : 'inactive')));
        svg.appendChild(text(37, 72, 'ARM64', 'block-text small' + (arm64Active ? '' : ' inactive')));

        svg.appendChild(rect(72, 55, 55, 25, 'block ' + (riscvActive ? 'active riscv' : 'inactive')));
        svg.appendChild(text(100, 72, 'RISC-V', 'block-text small' + (riscvActive ? '' : ' inactive')));

        svg.appendChild(rect(135, 55, 55, 25, 'block ' + (x86Active ? 'active x86' : 'inactive')));
        svg.appendChild(text(162, 72, 'x86-64', 'block-text small' + (x86Active ? '' : ' inactive')));

        // Arrows from fetch to decoders
        svg.appendChild(path('M100 40 L37 55', 'arrow ' + (arm64Active ? 'active' : 'inactive')));
        svg.appendChild(path('M100 40 L100 55', 'arrow ' + (riscvActive ? 'active' : 'inactive')));
        svg.appendChild(path('M100 40 L162 55', 'arrow ' + (x86Active ? 'active' : 'inactive')));

        // Arrow from active decoder to rename
        if (arm64Active) {
            svg.appendChild(path('M37 80 L100 95', 'arrow active'));
        } else if (riscvActive) {
            svg.appendChild(path('M100 80 L100 95', 'arrow active'));
        } else if (x86Active) {
            svg.appendChild(path('M162 80 L100 95', 'arrow active'));
        }
    }

    // Rename/Dispatch
    svg.appendChild(rect(10, 95, 180, 25, 'block active'));
    svg.appendChild(text(100, 112, 'Rename / Dispatch', 'block-text small'));
    svg.appendChild(path('M100 120 L100 135', 'arrow active'));

    // ROB
    svg.appendChild(rect(10, 135, 85, 25, 'block active'));
    svg.appendChild(text(52, 152, 'ROB', 'block-text small'));

    // Register File
    svg.appendChild(rect(105, 135, 85, 25, 'block active'));
    svg.appendChild(text(147, 152, 'Register File', 'block-text small'));
    svg.appendChild(path('M100 160 L100 175', 'arrow active'));

    // Execution Units
    svg.appendChild(rect(10, 175, 180, 25, 'block active'));
    svg.appendChild(text(100, 192, 'Execution Units', 'block-text small'));
    svg.appendChild(path('M100 200 L100 215', 'arrow active'));

    // L1 Cache
    svg.appendChild(rect(10, 215, 180, 20, 'block active'));
    svg.appendChild(text(100, 229, 'L1 Cache', 'block-text small'));

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
