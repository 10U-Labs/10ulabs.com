let rackHeight = 12;
let rackCount = 3;
let placedParts = [];
let selectedPartId = null;

const defaultColors = {
    'blank-panel-1u': '#bdc3c7',
    'blank-panel-2u': '#95a5a6',
    'custom': '#7f8c8d',
    'display': '#1abc9c',
    'nas': '#9b59b6',
    'patch-panel': '#34495e',
    'pdu': '#e67e22',
    'san': '#8e44ad',
    'server': '#3498db',
    'shelf': '#16a085',
    'switch': '#f39c12',
    'ups': '#e74c3c',
    'venting-1u': '#95a5a6',
    'venting-2u': '#7f8c8d',
    'wifi-bridge': '#2ecc71'
};

function initRacks() {
    const racksContainer = document.getElementById('racksContainer');
    racksContainer.innerHTML = '';

    for (let rackId = 1; rackId <= rackCount; rackId++) {
        const rackSection = document.createElement('div');
        rackSection.className = 'rack-section';

        const rackTitle = document.createElement('h3');
        rackTitle.className = 'rack-title';
        rackTitle.textContent = `Rack ${rackId}`;
        rackSection.appendChild(rackTitle);

        const rackContainer = document.createElement('div');
        rackContainer.className = 'rack-container';

        const rack = document.createElement('div');
        rack.className = 'rack';
        rack.id = `rack${rackId}`;
        rack.dataset.rackId = rackId;

        for (let i = 1; i <= rackHeight; i++) {
            const slot = document.createElement('div');
            slot.className = 'rack-slot';
            slot.dataset.slot = i;
            slot.dataset.rackId = rackId;

            const slotNumber = document.createElement('div');
            slotNumber.className = 'rack-slot-number';
            slotNumber.textContent = i;
            slot.appendChild(slotNumber);

            slot.addEventListener('dragover', handleDragOver);
            slot.addEventListener('drop', handleDrop);
            slot.addEventListener('dragleave', handleDragLeave);

            rack.appendChild(slot);
        }

        rackContainer.appendChild(rack);
        rackSection.appendChild(rackContainer);
        racksContainer.appendChild(rackSection);
    }
}

function handleDragStart(e) {
    const element = e.currentTarget;
    const partType = element.dataset.part;
    const partSize = element.dataset.size;
    const partId = element.dataset.partId;
    const rackId = element.dataset.rackId;

    if (partType) {
        e.dataTransfer.setData('partType', partType);
        e.dataTransfer.setData('partSize', partSize);
        e.dataTransfer.effectAllowed = 'copy';
        sessionStorage.setItem('draggingPartSize', partSize);
    } else if (partId) {
        e.dataTransfer.setData('existingPart', partId);
        e.dataTransfer.setData('sourceRackId', rackId);
        e.dataTransfer.effectAllowed = 'move';
        element.classList.add('dragging');
        sessionStorage.setItem('draggingPartId', partId);
        sessionStorage.setItem('draggingPartRackId', rackId);
    }

    document.querySelectorAll('.placed-part').forEach(comp => {
        if (comp !== element) {
            comp.style.pointerEvents = 'none';
        }
    });
}

function handleDragEnd(e) {
    const element = e.currentTarget;
    element.classList.remove('dragging');
    sessionStorage.removeItem('draggingPartSize');
    sessionStorage.removeItem('draggingPartId');
    sessionStorage.removeItem('draggingPartRackId');
    document.querySelectorAll('.rack-slot').forEach(slot => {
        slot.classList.remove('drag-over', 'drag-over-invalid');
    });

    document.querySelectorAll('.placed-part').forEach(comp => {
        comp.style.pointerEvents = '';
    });
}

function getAffectedSlots(startSlot, partSize) {
    const slots = [];
    for (let i = startSlot; i < startSlot + partSize; i++) {
        slots.push(i);
    }
    return slots;
}

function isValidPlacement(rackId, startSlot, partSize, excludeId = null) {
    if (startSlot + partSize - 1 > rackHeight) {
        return false;
    }

    const rackParts = placedParts.filter(p => p.rackId === rackId);

    for (let i = startSlot; i < startSlot + partSize; i++) {
        for (const part of rackParts) {
            if (excludeId && part.id === excludeId) continue;
            const partEnd = part.startSlot + part.size - 1;
            if (i >= part.startSlot && i <= partEnd) {
                return false;
            }
        }
    }

    return true;
}

function handleDragOver(e) {
    e.preventDefault();

    const currentSlot = parseInt(e.currentTarget.dataset.slot);
    const targetRackId = parseInt(e.currentTarget.dataset.rackId);
    const existingPartId = e.dataTransfer.types.includes('existingpart') ?
        sessionStorage.getItem('draggingPartId') : null;

    let partSize = 1;
    if (existingPartId) {
        const part = placedParts.find(c => c.id === existingPartId);
        partSize = part ? part.size : 1;
    } else if (e.dataTransfer.types.includes('partsize')) {
        partSize = parseInt(sessionStorage.getItem('draggingPartSize') || '1');
    }

    let bestStartSlot = currentSlot;
    let isValid = isValidPlacement(targetRackId, currentSlot, partSize, existingPartId);

    if (!isValid && partSize > 1) {
        for (let offset = 1; offset < partSize; offset++) {
            const tryStartSlot = currentSlot - offset;
            if (tryStartSlot >= 1) {
                const tryEndSlot = tryStartSlot + partSize - 1;
                if (tryEndSlot >= currentSlot) {
                    if (isValidPlacement(targetRackId, tryStartSlot, partSize, existingPartId)) {
                        bestStartSlot = tryStartSlot;
                        isValid = true;
                        break;
                    }
                }
            }
        }
    }

    const affectedSlots = getAffectedSlots(bestStartSlot, partSize);

    document.querySelectorAll('.rack-slot').forEach(slot => {
        slot.classList.remove('drag-over', 'drag-over-invalid');
    });

    affectedSlots.forEach(slotNum => {
        const slotElement = document.querySelector(`.rack-slot[data-slot="${slotNum}"][data-rack-id="${targetRackId}"]`);
        if (slotElement) {
            if (isValid) {
                slotElement.classList.add('drag-over');
            } else {
                slotElement.classList.add('drag-over-invalid');
            }
        }
    });

    e.dataTransfer.dropEffect = isValid ? 'copy' : 'none';
}

function handleDragLeave(e) {
    if (!e.currentTarget.contains(e.relatedTarget)) {
        document.querySelectorAll('.rack-slot').forEach(slot => {
            slot.classList.remove('drag-over', 'drag-over-invalid');
        });
    }
}

function handleDrop(e) {
    e.preventDefault();
    document.querySelectorAll('.rack-slot').forEach(slot => {
        slot.classList.remove('drag-over', 'drag-over-invalid');
    });

    const slot = parseInt(e.currentTarget.dataset.slot);
    const targetRackId = parseInt(e.currentTarget.dataset.rackId);
    const existingPartId = e.dataTransfer.getData('existingPart');

    if (existingPartId) {
        const part = placedParts.find(c => c.id === existingPartId);
        const partSize = part ? part.size : 1;

        let bestStartSlot = slot;
        if (!isValidPlacement(targetRackId, slot, partSize, existingPartId) && partSize > 1) {
            for (let offset = 1; offset < partSize; offset++) {
                const tryStartSlot = slot - offset;
                if (tryStartSlot >= 1) {
                    const tryEndSlot = tryStartSlot + partSize - 1;
                    if (tryEndSlot >= slot) {
                        if (isValidPlacement(targetRackId, tryStartSlot, partSize, existingPartId)) {
                            bestStartSlot = tryStartSlot;
                            break;
                        }
                    }
                }
            }
        }

        movePart(existingPartId, targetRackId, bestStartSlot);
    } else {
        const partType = e.dataTransfer.getData('partType');
        const partSize = parseInt(e.dataTransfer.getData('partSize'));

        let bestStartSlot = slot;
        if (!canPlacePart(targetRackId, slot, partSize) && partSize > 1) {
            for (let offset = 1; offset < partSize; offset++) {
                const tryStartSlot = slot - offset;
                if (tryStartSlot >= 1) {
                    const tryEndSlot = tryStartSlot + partSize - 1;
                    if (tryEndSlot >= slot) {
                        if (canPlacePart(targetRackId, tryStartSlot, partSize)) {
                            bestStartSlot = tryStartSlot;
                            break;
                        }
                    }
                }
            }
        }

        addPart(partType, partSize, targetRackId, bestStartSlot);
    }
}

function addPart(type, size, rackId, startSlot) {
    if (!canPlacePart(rackId, startSlot, size)) {
        alert(`Cannot place part: slots ${startSlot} to ${startSlot + size - 1} are not available or exceed rack height.`);
        return;
    }

    const part = {
        id: Date.now().toString(),
        type: type,
        size: size,
        rackId: rackId,
        startSlot: startSlot,
        customName: null,
        customColor: null
    };

    placedParts.push(part);
    renderParts();
}

function movePart(partId, newRackId, newStartSlot) {
    const part = placedParts.find(c => c.id === partId);
    if (!part) return;

    const otherParts = placedParts.filter(c => c.id !== partId || c.rackId !== newRackId);

    for (let i = newStartSlot; i < newStartSlot + part.size; i++) {
        if (i > rackHeight) {
            alert(`Cannot place part: exceeds rack height.`);
            return;
        }

        for (const other of otherParts) {
            if (other.rackId !== newRackId) continue;
            const otherEnd = other.startSlot + other.size - 1;
            if (i >= other.startSlot && i <= otherEnd) {
                alert(`Cannot place part: slot ${i} is occupied.`);
                return;
            }
        }
    }

    part.rackId = newRackId;
    part.startSlot = newStartSlot;
    renderParts();
}

function canPlacePart(rackId, startSlot, size, excludeId = null) {
    const endSlot = startSlot + size - 1;

    if (endSlot > rackHeight) {
        return false;
    }

    const rackParts = placedParts.filter(p => p.rackId === rackId);

    for (let i = startSlot; i < startSlot + size; i++) {
        for (const part of rackParts) {
            if (excludeId && part.id === excludeId) continue;
            const partEnd = part.startSlot + part.size - 1;
            if (i >= part.startSlot && i <= partEnd) {
                return false;
            }
        }
    }

    return true;
}

function removePart(partId) {
    placedParts = placedParts.filter(c => c.id !== partId);
    if (selectedPartId === partId) {
        deselectPart();
    }
    renderParts();
}

function selectPart(partId) {
    selectedPartId = partId;
    const part = placedParts.find(c => c.id === partId);

    if (part) {
        document.getElementById('partName').value = part.customName || getPartName(part.type);
        document.getElementById('partColor').value = part.customColor || defaultColors[part.type];
        document.getElementById('partHeightValue').textContent = `${part.size}U`;
        document.getElementById('detailsPanel').style.display = 'block';
        document.getElementById('mainArea').classList.remove('no-selection');
    }

    renderParts();
}

function deselectPart() {
    selectedPartId = null;
    document.getElementById('detailsPanel').style.display = 'none';
    document.getElementById('mainArea').classList.add('no-selection');
    renderParts();
}

function updatePartName() {
    if (!selectedPartId) return;

    const part = placedParts.find(c => c.id === selectedPartId);
    if (part) {
        const newName = document.getElementById('partName').value.trim();
        part.customName = newName || null;
        renderParts();
    }
}

function updatePartColor() {
    if (!selectedPartId) return;

    const part = placedParts.find(c => c.id === selectedPartId);
    if (part) {
        const newColor = document.getElementById('partColor').value;
        part.customColor = newColor;
        renderParts();
    }
}

function updatePartHeight(delta) {
    if (!selectedPartId) return;

    const part = placedParts.find(c => c.id === selectedPartId);
    if (part) {
        const newHeight = part.size + delta;

        if (newHeight < 1 || newHeight > 10) {
            alert('Height must be between 1U and 10U');
            return;
        }

        if (newHeight !== part.size) {
            const otherParts = placedParts.filter(c => !(c.id === selectedPartId && c.rackId === part.rackId));

            if (delta > 0) {
                const expandDownStartSlot = part.startSlot - delta;
                const expandUpEndSlot = part.startSlot + part.size - 1 + delta;

                let canExpandDown = expandDownStartSlot >= 1;
                let canExpandUp = expandUpEndSlot <= rackHeight;

                if (canExpandDown) {
                    let hasConflictDown = false;
                    for (let i = expandDownStartSlot; i < part.startSlot; i++) {
                        for (const other of otherParts) {
                            if (other.rackId !== part.rackId) continue;
                            const otherEnd = other.startSlot + other.size - 1;
                            if (i >= other.startSlot && i <= otherEnd) {
                                hasConflictDown = true;
                                break;
                            }
                        }
                        if (hasConflictDown) break;
                    }
                    canExpandDown = !hasConflictDown;
                }

                if (canExpandUp) {
                    let hasConflictUp = false;
                    const currentEnd = part.startSlot + part.size - 1;
                    for (let i = currentEnd + 1; i <= expandUpEndSlot; i++) {
                        for (const other of otherParts) {
                            if (other.rackId !== part.rackId) continue;
                            const otherEnd = other.startSlot + other.size - 1;
                            if (i >= other.startSlot && i <= otherEnd) {
                                hasConflictUp = true;
                                break;
                            }
                        }
                        if (hasConflictUp) break;
                    }
                    canExpandUp = !hasConflictUp;
                }

                if (canExpandDown) {
                    part.startSlot = expandDownStartSlot;
                    part.size = newHeight;
                } else if (canExpandUp) {
                    part.size = newHeight;
                } else {
                    alert(`Cannot change height: no free slots available above or below`);
                    return;
                }
            } else {
                part.size = newHeight;
            }

            document.getElementById('partHeightValue').textContent = `${newHeight}U`;
        }

        renderParts();
    }
}

function renderParts() {
    document.querySelectorAll('.placed-part').forEach(el => el.remove());

    const slotHeight = 40;

    placedParts.forEach(part => {
        const rack = document.getElementById(`rack${part.rackId}`);
        if (!rack) return;

        const partEl = document.createElement('div');
        partEl.className = `placed-part`;
        partEl.dataset.partId = part.id;
        partEl.dataset.rackId = part.rackId;
        partEl.draggable = true;
        partEl.style.pointerEvents = '';

        if (part.id === selectedPartId) {
            partEl.classList.add('selected');
        }

        const bottomPosition = (part.startSlot - 1) * slotHeight;
        partEl.style.bottom = `${bottomPosition}px`;
        partEl.style.height = `${part.size * slotHeight}px`;

        const color = part.customColor || defaultColors[part.type];
        partEl.style.background = color;
        partEl.style.border = `2px solid ${adjustBrightness(color, -20)}`;

        const nameSpan = document.createElement('span');
        nameSpan.textContent = part.customName || getPartName(part.type);

        const removeBtn = document.createElement('button');
        removeBtn.className = 'part-remove';
        removeBtn.textContent = '×';
        removeBtn.onclick = (e) => {
            e.stopPropagation();
            removePart(part.id);
        };

        partEl.appendChild(nameSpan);
        partEl.appendChild(removeBtn);

        partEl.addEventListener('dragstart', handleDragStart);
        partEl.addEventListener('dragend', handleDragEnd);
        partEl.addEventListener('click', (e) => {
            if (e.target !== removeBtn) {
                selectPart(part.id);
            }
        });

        rack.appendChild(partEl);
    });
}

function getPartName(type) {
    const names = {
        'blank-panel-1u': 'Blank Panel (1U)',
        'blank-panel-2u': 'Blank Panel (2U)',
        'custom': 'Custom Part',
        'display': 'Display',
        'nas': 'NAS',
        'patch-panel': 'Patch Panel',
        'pdu': 'PDU',
        'san': 'SAN',
        'server': 'Server',
        'shelf': 'Shelf',
        'switch': 'Switch',
        'ups': 'UPS',
        'venting-1u': 'Venting Panel (1U)',
        'venting-2u': 'Venting Panel (2U)',
        'wifi-bridge': 'WiFi Bridge'
    };
    return names[type] || type;
}

function adjustBrightness(color, amount) {
    const num = parseInt(color.replace('#', ''), 16);
    const r = Math.max(0, Math.min(255, (num >> 16) + amount));
    const g = Math.max(0, Math.min(255, ((num >> 8) & 0x00FF) + amount));
    const b = Math.max(0, Math.min(255, (num & 0x0000FF) + amount));
    return '#' + ((r << 16) | (g << 8) | b).toString(16).padStart(6, '0');
}

function updateHeight(delta) {
    const newHeight = rackHeight + delta;

    if (newHeight < 1 || newHeight > 42) {
        return;
    }

    for (let rackId = 1; rackId <= rackCount; rackId++) {
        const partsInRack = placedParts.filter(p => p.rackId === rackId);
        const totalUsedSlots = partsInRack.reduce((sum, p) => sum + p.size, 0);

        if (totalUsedSlots > newHeight) {
            alert(`Cannot reduce height to ${newHeight}U: Rack ${rackId} has ${totalUsedSlots}U of parts that won't fit. Please remove some parts first.`);
            return;
        }
    }

    for (let rackId = 1; rackId <= rackCount; rackId++) {
        const partsInRack = placedParts.filter(p => p.rackId === rackId);
        const partsToRelocate = partsInRack.filter(p => p.startSlot > newHeight || (p.startSlot + p.size - 1) > newHeight);

        if (partsToRelocate.length > 0) {
            partsToRelocate.sort((a, b) => b.startSlot - a.startSlot);

            for (const part of partsToRelocate) {
                let foundSlot = false;
                for (let slot = newHeight - part.size + 1; slot >= 1; slot--) {
                    const tempPlacedParts = placedParts.filter(p => p.id !== part.id);
                    const canPlace = tempPlacedParts.every(p => {
                        if (p.rackId !== rackId) return true;
                        const pEnd = p.startSlot + p.size - 1;
                        const partEnd = slot + part.size - 1;
                        return partEnd < p.startSlot || slot > pEnd;
                    });

                    if (canPlace) {
                        part.startSlot = slot;
                        foundSlot = true;
                        break;
                    }
                }

                if (!foundSlot) {
                    alert(`Cannot reduce height to ${newHeight}U: Unable to automatically reposition parts in Rack ${rackId}. Please manually rearrange parts first.`);
                    return;
                }
            }
        }
    }

    rackHeight = newHeight;
    document.getElementById('heightValue').textContent = `${rackHeight}U`;
    initRacks();
    renderParts();
}

function resetAllRacks() {
    if (placedParts.length > 0) {
        if (confirm('Are you sure you want to remove all parts from all racks?')) {
            placedParts = [];
            deselectPart();
            renderParts();
        }
    }
}

function updateRackCount(delta) {
    const newCount = rackCount + delta;

    if (newCount < 1) {
        return;
    }

    if (delta < 0) {
        const partsInRemovedRacks = placedParts.filter(p => p.rackId > newCount);
        if (partsInRemovedRacks.length > 0) {
            alert(`Cannot remove rack${newCount < rackCount - 1 ? 's' : ''}: ${partsInRemovedRacks.length} part${partsInRemovedRacks.length > 1 ? 's' : ''} would be removed. Please move or delete them first.`);
            return;
        }
    }

    rackCount = newCount;
    document.getElementById('rackCountValue').textContent = `${rackCount} Rack${rackCount > 1 ? 's' : ''}`;
    initRacks();
    renderParts();
}

document.getElementById('increaseHeight').addEventListener('click', () => updateHeight(1));
document.getElementById('decreaseHeight').addEventListener('click', () => updateHeight(-1));

document.getElementById('increaseRackCount').addEventListener('click', () => updateRackCount(1));
document.getElementById('decreaseRackCount').addEventListener('click', () => updateRackCount(-1));

document.querySelectorAll('.part-item').forEach(item => {
    item.addEventListener('dragstart', handleDragStart);
});

initRacks();
document.getElementById('mainArea').classList.add('no-selection');

document.getElementById('partName').addEventListener('blur', updatePartName);
document.getElementById('partName').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        updatePartName();
        e.target.blur();
    }
});

document.getElementById('partColor').addEventListener('change', updatePartColor);
document.getElementById('increasePartHeight').addEventListener('click', () => updatePartHeight(1));
document.getElementById('decreasePartHeight').addEventListener('click', () => updatePartHeight(-1));

const API_BASE_URL = 'https://api.10ulabs.com';

function getConfiguration() {
    const config = {
        rackHeight: rackHeight,
        rackCount: rackCount,
        placedParts: placedParts.map(part => ({
            type: part.type,
            size: part.size,
            rackId: part.rackId,
            startSlot: part.startSlot,
            customName: part.customName,
            customColor: part.customColor
        }))
    };
    return config;
}

function loadConfiguration(config) {
    rackHeight = config.rackHeight;
    rackCount = config.rackCount;
    placedParts = config.placedParts.map((part, index) => ({
        id: Date.now().toString() + index,
        type: part.type,
        size: part.size,
        rackId: part.rackId,
        startSlot: part.startSlot,
        customName: part.customName,
        customColor: part.customColor
    }));
    document.getElementById('heightValue').textContent = `${rackHeight}U`;
    document.getElementById('rackCountValue').textContent = `${rackCount} Rack${rackCount > 1 ? 's' : ''}`;
    initRacks();
    renderParts();
}

function saveConfiguration() {
    const config = getConfiguration();
    fetch(`${API_BASE_URL}/v1/rack-designer/configurations`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ configuration: config })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const newUrl = `${window.location.origin}${window.location.pathname}?c=${data.config_hash}`;
            window.history.pushState({ config_hash: data.config_hash }, '', newUrl);
            alert(`Configuration saved! Share this URL:\n${newUrl}`);
        } else {
            alert(`Failed to save configuration: ${data.error}`);
        }
    })
    .catch(error => {
        alert(`Error saving configuration: ${error.message}`);
    });
}

function loadConfigurationFromUrl() {
    const urlParams = new URLSearchParams(window.location.search);
    const configHash = urlParams.get('c');
    if (!configHash) {
        return;
    }
    fetch(`${API_BASE_URL}/v1/rack-designer/configurations/${configHash}`)
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadConfiguration(data.configuration);
        } else {
            alert(`Failed to load configuration: ${data.error}`);
        }
    })
    .catch(error => {
        alert(`Error loading configuration: ${error.message}`);
    });
}

loadConfigurationFromUrl();
