var API_BASE_URL = 'https://api.10ulabs.com';

var socConfigLoaded = false;

var PERSONAS = ['desktop64', 'mobile64', 'riscv'];
var PERSONA_LABELS = {
    'riscv': 'RISC-V',
    'desktop64': 'Desktop64',
    'mobile64': 'Mobile64'
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
    svg.setAttribute('viewBox', '0 0 220 280');
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
    var mobile64Active = activeIsa === 'mobile64';
    var riscvActive = activeIsa === 'riscv';
    var desktop64Active = activeIsa === 'desktop64';

    // Instruction Fetch
    svg.appendChild(rect(10, 10, 200, 25, 'block active'));
    svg.appendChild(text(110, 27, 'Instruction Fetch (16B/cyc)', 'block-text small'));

    if (isTriMode) {
        // Arrow from Instruction Fetch to active decoder (diagonal for Mobile64/Desktop64, vertical for RISC-V)
        if (mobile64Active) {
            svg.appendChild(path('M110 35 L40 48', 'arrow active'));
        } else if (desktop64Active) {
            svg.appendChild(path('M110 35 L180 48', 'arrow active'));
        } else {
            svg.appendChild(path('M110 35 L110 48', 'arrow active'));
        }
    } else {
        svg.appendChild(path('M110 35 L110 48', 'arrow active'));
    }

    if (isTriMode) {
        // Three parallel decode lanes (0 extra stages)
        svg.appendChild(rect(10, 48, 60, 28, 'block ' + (mobile64Active ? 'active mobile64' : 'inactive')));
        svg.appendChild(text(40, 60, 'Mobile64', 'block-text small' + (mobile64Active ? '' : ' inactive')));
        svg.appendChild(text(40, 70, 'Decode', 'block-text tiny' + (mobile64Active ? '' : ' inactive')));

        svg.appendChild(rect(80, 48, 60, 28, 'block ' + (riscvActive ? 'active riscv' : 'inactive')));
        svg.appendChild(text(110, 60, 'RISC-V', 'block-text small' + (riscvActive ? '' : ' inactive')));
        svg.appendChild(text(110, 70, 'Decode', 'block-text tiny' + (riscvActive ? '' : ' inactive')));

        svg.appendChild(rect(150, 48, 60, 28, 'block ' + (desktop64Active ? 'active desktop64' : 'inactive')));
        svg.appendChild(text(180, 60, 'Desktop64', 'block-text small' + (desktop64Active ? '' : ' inactive')));
        svg.appendChild(text(180, 70, 'Decode', 'block-text tiny' + (desktop64Active ? '' : ' inactive')));

        // Arrows from active decoder to µop queue
        if (mobile64Active) {
            svg.appendChild(path('M40 76 L110 90', 'arrow active'));
        } else if (riscvActive) {
            svg.appendChild(path('M110 76 L110 90', 'arrow active'));
        } else if (desktop64Active) {
            svg.appendChild(path('M180 76 L110 90', 'arrow active'));
        }

        // Micro-op queue - all decoders emit RISC-V µops
        svg.appendChild(rect(10, 90, 200, 22, 'block active'));
        svg.appendChild(text(110, 105, 'RISC-V Micro-op Queue', 'block-text small'));

        // Flags predictor annotation for Desktop64/Mobile64 (reduces overhead)
        if (desktop64Active) {
            svg.appendChild(rect(10, 118, 200, 16, 'block active optimization'));
            svg.appendChild(text(110, 129, 'Flags Predictor (0.15 µops/use vs 3)', 'block-text tiny'));
            svg.appendChild(path('M110 112 L110 118', 'arrow active'));
            svg.appendChild(path('M110 134 L110 145', 'arrow active'));
        } else if (mobile64Active) {
            svg.appendChild(rect(10, 118, 200, 16, 'block active optimization'));
            svg.appendChild(text(110, 129, 'Flags Predictor (0.1 µops/use)', 'block-text tiny'));
            svg.appendChild(path('M110 112 L110 118', 'arrow active'));
            svg.appendChild(path('M110 134 L110 145', 'arrow active'));
        } else {
            svg.appendChild(path('M110 112 L110 145', 'arrow active'));
        }
    } else {
        // Native core: single optimized decoder for that ISA (hypothetical reference)
        svg.appendChild(rect(40, 48, 140, 28, 'block active'));
        svg.appendChild(text(110, 60, 'Native ISA Decoder', 'block-text small'));
        svg.appendChild(text(110, 70, '(hypothetical reference)', 'block-text tiny'));
        svg.appendChild(path('M110 76 L110 90', 'arrow active'));

        // Direct to backend µops
        svg.appendChild(rect(10, 90, 200, 22, 'block active'));
        svg.appendChild(text(110, 105, 'Native Micro-ops', 'block-text small'));
        svg.appendChild(path('M110 112 L110 145', 'arrow active'));
    }

    // Rename/Dispatch - shared backend starts here
    svg.appendChild(rect(10, 145, 200, 22, 'block active'));
    svg.appendChild(text(110, 160, 'Rename / Dispatch (3-wide)', 'block-text small'));
    svg.appendChild(path('M110 167 L110 180', 'arrow active'));

    // ROB + Register File
    svg.appendChild(rect(10, 180, 95, 22, 'block active'));
    svg.appendChild(text(57, 195, 'ROB (128)', 'block-text small'));
    svg.appendChild(rect(115, 180, 95, 22, 'block active'));
    svg.appendChild(text(162, 195, 'Registers', 'block-text small'));
    svg.appendChild(path('M110 202 L110 215', 'arrow active'));

    // Execution Units
    svg.appendChild(rect(10, 215, 200, 22, 'block active'));
    svg.appendChild(text(110, 230, 'Execution Units (3 ALU, 2 LD, 1 ST)', 'block-text tiny'));
    svg.appendChild(path('M110 237 L110 250', 'arrow active'));

    // Load-Store Unit with TSO mode for Desktop64
    if (isTriMode && desktop64Active) {
        svg.appendChild(rect(10, 250, 200, 22, 'block active optimization'));
        svg.appendChild(text(110, 265, 'Load-Store [HW TSO: 0 fence overhead]', 'block-text tiny'));
    } else {
        svg.appendChild(rect(10, 250, 200, 22, 'block active'));
        svg.appendChild(text(110, 265, 'Load-Store Unit', 'block-text small'));
    }

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
    container.appendChild(createDiagramCard('', '', '', 'mobile64'));
    container.appendChild(createDiagramCard('', '', '', 'riscv'));
    container.appendChild(createDiagramCard('', '', '', 'desktop64'));
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
