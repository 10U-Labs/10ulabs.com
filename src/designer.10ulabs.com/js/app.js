let rackHeight = 12;
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

function initRack() {
    const rack = document.getElementById('rack');
    rack.innerHTML = '';

    for (let i = 1; i <= rackHeight; i++) {
        const slot = document.createElement('div');
        slot.className = 'rack-slot';
        slot.dataset.slot = i;

        const slotNumber = document.createElement('div');
        slotNumber.className = 'rack-slot-number';
        slotNumber.textContent = i;
        slot.appendChild(slotNumber);

        slot.addEventListener('dragover', handleDragOver);
        slot.addEventListener('drop', handleDrop);
        slot.addEventListener('dragleave', handleDragLeave);

        rack.appendChild(slot);
    }
}

function handleDragStart(e) {
    const partType = e.target.dataset.part;
    const partSize = e.target.dataset.size;

    if (partType) {
        e.dataTransfer.setData('partType', partType);
        e.dataTransfer.setData('partSize', partSize);
        e.dataTransfer.effectAllowed = 'copy';
        sessionStorage.setItem('draggingPartSize', partSize);
    } else {
        const partId = e.target.dataset.partId;
        e.dataTransfer.setData('existingPart', partId);
        e.dataTransfer.effectAllowed = 'move';
        e.target.classList.add('dragging');
        sessionStorage.setItem('draggingPartId', partId);
    }

    document.querySelectorAll('.placed-part').forEach(comp => {
        comp.style.pointerEvents = 'none';
    });
}

function handleDragEnd(e) {
    e.target.classList.remove('dragging');
    sessionStorage.removeItem('draggingPartSize');
    sessionStorage.removeItem('draggingPartId');
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

function isValidPlacement(startSlot, partSize, excludeId = null) {
    if (startSlot + partSize - 1 > rackHeight) {
        return false;
    }

    for (let i = startSlot; i < startSlot + partSize; i++) {
        for (const part of placedParts) {
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
    const existingPartId = e.dataTransfer.types.includes('existingpart') ?
        sessionStorage.getItem('draggingPartId') : null;

    let partSize = 1;
    if (existingPartId) {
        const part = placedParts.find(c => c.id === existingPartId);
        partSize = part ? part.size : 1;
    } else if (e.dataTransfer.types.includes('partsize')) {
        partSize = parseInt(sessionStorage.getItem('draggingPartSize') || '1');
    }

    const affectedSlots = getAffectedSlots(currentSlot, partSize);
    const isValid = isValidPlacement(currentSlot, partSize, existingPartId);

    document.querySelectorAll('.rack-slot').forEach(slot => {
        slot.classList.remove('drag-over', 'drag-over-invalid');
    });

    affectedSlots.forEach(slotNum => {
        const slotElement = document.querySelector(`.rack-slot[data-slot="${slotNum}"]`);
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
    const existingPartId = e.dataTransfer.getData('existingPart');

    if (existingPartId) {
        movePart(existingPartId, slot);
    } else {
        const partType = e.dataTransfer.getData('partType');
        const partSize = parseInt(e.dataTransfer.getData('partSize'));
        addPart(partType, partSize, slot);
    }
}

function addPart(type, size, startSlot) {
    if (!canPlacePart(startSlot, size)) {
        alert(`Cannot place part: slots ${startSlot} to ${startSlot + size - 1} are not available or exceed rack height.`);
        return;
    }

    const part = {
        id: Date.now().toString(),
        type: type,
        size: size,
        startSlot: startSlot,
        customName: null,
        customColor: null
    };

    placedParts.push(part);
    renderParts();
}

function movePart(partId, newStartSlot) {
    const part = placedParts.find(c => c.id === partId);
    if (!part) return;

    const otherParts = placedParts.filter(c => c.id !== partId);

    for (let i = newStartSlot; i < newStartSlot + part.size; i++) {
        if (i > rackHeight) {
            alert(`Cannot place part: exceeds rack height.`);
            return;
        }

        for (const other of otherParts) {
            const otherEnd = other.startSlot + other.size - 1;
            if (i >= other.startSlot && i <= otherEnd) {
                alert(`Cannot place part: slot ${i} is occupied.`);
                return;
            }
        }
    }

    part.startSlot = newStartSlot;
    renderParts();
}

function canPlacePart(startSlot, size, excludeId = null) {
    const endSlot = startSlot + size - 1;

    if (endSlot > rackHeight) {
        return false;
    }

    for (let i = startSlot; i < startSlot + size; i++) {
        for (const part of placedParts) {
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
            const otherParts = placedParts.filter(c => c.id !== selectedPartId);

            if (delta > 0) {
                const expandDownStartSlot = part.startSlot - delta;
                const expandUpEndSlot = part.startSlot + part.size - 1 + delta;

                let canExpandDown = expandDownStartSlot >= 1;
                let canExpandUp = expandUpEndSlot <= rackHeight;

                if (canExpandDown) {
                    let hasConflictDown = false;
                    for (let i = expandDownStartSlot; i < part.startSlot; i++) {
                        for (const other of otherParts) {
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

function deletePart() {
    if (!selectedPartId) return;

    if (confirm('Are you sure you want to delete this part?')) {
        removePart(selectedPartId);
    }
}

function renderParts() {
    document.querySelectorAll('.placed-part').forEach(el => el.remove());

    const rack = document.getElementById('rack');
    const slotHeight = 40;

    placedParts.forEach(part => {
        const partEl = document.createElement('div');
        partEl.className = `placed-part`;
        partEl.dataset.partId = part.id;
        partEl.draggable = true;

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

    const maxUsedSlot = placedParts.reduce((max, c) => {
        return Math.max(max, c.startSlot + c.size - 1);
    }, 0);

    if (newHeight < maxUsedSlot) {
        alert(`Cannot reduce height below ${maxUsedSlot}U: parts are using those slots.`);
        return;
    }

    rackHeight = newHeight;
    document.getElementById('heightValue').textContent = `${rackHeight}U`;
    initRack();
    renderParts();
}

function resetRack() {
    if (placedParts.length > 0) {
        if (confirm('Are you sure you want to remove all parts from the rack?')) {
            placedParts = [];
            deselectPart();
            renderParts();
        }
    }
}

document.getElementById('increaseHeight').addEventListener('click', () => updateHeight(1));
document.getElementById('decreaseHeight').addEventListener('click', () => updateHeight(-1));

document.querySelectorAll('.part-item').forEach(item => {
    item.addEventListener('dragstart', handleDragStart);
});

initRack();
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
