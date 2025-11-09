let rackHeight = 5;
let placedComponents = [];
let selectedComponentId = null;

const defaultColors = {
    'server': '#3498db',
    'wifi-bridge': '#2ecc71',
    'ventilation': '#95a5a6',
    'ups': '#e74c3c',
    'switch': '#f39c12'
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
    const componentType = e.target.dataset.component;
    const componentSize = e.target.dataset.size;

    if (componentType) {
        e.dataTransfer.setData('componentType', componentType);
        e.dataTransfer.setData('componentSize', componentSize);
        e.dataTransfer.effectAllowed = 'copy';
    } else {
        const componentId = e.target.dataset.componentId;
        e.dataTransfer.setData('existingComponent', componentId);
        e.dataTransfer.effectAllowed = 'move';
        e.target.classList.add('dragging');
    }
}

function handleDragEnd(e) {
    e.target.classList.remove('dragging');
}

function handleDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'copy';
    e.currentTarget.classList.add('drag-over');
}

function handleDragLeave(e) {
    e.currentTarget.classList.remove('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    e.currentTarget.classList.remove('drag-over');

    const slot = parseInt(e.currentTarget.dataset.slot);
    const existingComponentId = e.dataTransfer.getData('existingComponent');

    if (existingComponentId) {
        moveComponent(existingComponentId, slot);
    } else {
        const componentType = e.dataTransfer.getData('componentType');
        const componentSize = parseInt(e.dataTransfer.getData('componentSize'));
        addComponent(componentType, componentSize, slot);
    }
}

function addComponent(type, size, startSlot) {
    if (!canPlaceComponent(startSlot, size)) {
        alert(`Cannot place component: slots ${startSlot} to ${startSlot + size - 1} are not available or exceed rack height.`);
        return;
    }

    const component = {
        id: Date.now().toString(),
        type: type,
        size: size,
        startSlot: startSlot,
        customName: null,
        customColor: null
    };

    placedComponents.push(component);
    renderComponents();
}

function moveComponent(componentId, newStartSlot) {
    const component = placedComponents.find(c => c.id === componentId);
    if (!component) return;

    const otherComponents = placedComponents.filter(c => c.id !== componentId);

    for (let i = newStartSlot; i < newStartSlot + component.size; i++) {
        if (i > rackHeight) {
            alert(`Cannot place component: exceeds rack height.`);
            return;
        }

        for (const other of otherComponents) {
            const otherEnd = other.startSlot + other.size - 1;
            if (i >= other.startSlot && i <= otherEnd) {
                alert(`Cannot place component: slot ${i} is occupied.`);
                return;
            }
        }
    }

    component.startSlot = newStartSlot;
    renderComponents();
}

function canPlaceComponent(startSlot, size, excludeId = null) {
    const endSlot = startSlot + size - 1;

    if (endSlot > rackHeight) {
        return false;
    }

    for (let i = startSlot; i < startSlot + size; i++) {
        for (const component of placedComponents) {
            if (excludeId && component.id === excludeId) continue;
            const componentEnd = component.startSlot + component.size - 1;
            if (i >= component.startSlot && i <= componentEnd) {
                return false;
            }
        }
    }

    return true;
}

function removeComponent(componentId) {
    placedComponents = placedComponents.filter(c => c.id !== componentId);
    if (selectedComponentId === componentId) {
        deselectComponent();
    }
    renderComponents();
}

function selectComponent(componentId) {
    selectedComponentId = componentId;
    const component = placedComponents.find(c => c.id === componentId);

    if (component) {
        document.getElementById('detailType').textContent = getComponentName(component.type);
        document.getElementById('detailSize').textContent = `${component.size}U`;
        document.getElementById('detailPosition').textContent = `${component.startSlot}U - ${component.startSlot + component.size - 1}U`;
        document.getElementById('componentName').value = component.customName || getComponentName(component.type);
        document.getElementById('componentColor').value = component.customColor || defaultColors[component.type];
        document.getElementById('detailsPanel').style.display = 'block';
        document.getElementById('mainArea').classList.remove('no-selection');
    }

    renderComponents();
}

function deselectComponent() {
    selectedComponentId = null;
    document.getElementById('detailsPanel').style.display = 'none';
    document.getElementById('mainArea').classList.add('no-selection');
    renderComponents();
}

function applyChanges() {
    if (!selectedComponentId) return;

    const component = placedComponents.find(c => c.id === selectedComponentId);
    if (component) {
        const newName = document.getElementById('componentName').value.trim();
        const newColor = document.getElementById('componentColor').value;

        component.customName = newName || null;
        component.customColor = newColor;

        renderComponents();
    }
}

function deleteComponent() {
    if (!selectedComponentId) return;

    if (confirm('Are you sure you want to delete this component?')) {
        removeComponent(selectedComponentId);
    }
}

function renderComponents() {
    document.querySelectorAll('.placed-component').forEach(el => el.remove());

    const rack = document.getElementById('rack');
    const slotHeight = 40;

    placedComponents.forEach(component => {
        const componentEl = document.createElement('div');
        componentEl.className = `placed-component`;
        componentEl.dataset.componentId = component.id;
        componentEl.draggable = true;

        if (component.id === selectedComponentId) {
            componentEl.classList.add('selected');
        }

        const bottomPosition = (component.startSlot - 1) * slotHeight;
        componentEl.style.bottom = `${bottomPosition}px`;
        componentEl.style.height = `${component.size * slotHeight}px`;

        const color = component.customColor || defaultColors[component.type];
        componentEl.style.background = color;
        componentEl.style.border = `2px solid ${adjustBrightness(color, -20)}`;

        const nameSpan = document.createElement('span');
        nameSpan.textContent = component.customName || getComponentName(component.type);

        const removeBtn = document.createElement('button');
        removeBtn.className = 'component-remove';
        removeBtn.textContent = '×';
        removeBtn.onclick = (e) => {
            e.stopPropagation();
            removeComponent(component.id);
        };

        componentEl.appendChild(nameSpan);
        componentEl.appendChild(removeBtn);

        componentEl.addEventListener('dragstart', handleDragStart);
        componentEl.addEventListener('dragend', handleDragEnd);
        componentEl.addEventListener('click', (e) => {
            if (e.target !== removeBtn) {
                selectComponent(component.id);
            }
        });

        rack.appendChild(componentEl);
    });
}

function getComponentName(type) {
    const names = {
        'server': 'Server',
        'wifi-bridge': 'WiFi Bridge',
        'ventilation': 'Ventilation Panel',
        'ups': 'UPS',
        'switch': 'Switch'
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

    const maxUsedSlot = placedComponents.reduce((max, c) => {
        return Math.max(max, c.startSlot + c.size - 1);
    }, 0);

    if (newHeight < maxUsedSlot) {
        alert(`Cannot reduce height below ${maxUsedSlot}U: components are using those slots.`);
        return;
    }

    rackHeight = newHeight;
    document.getElementById('heightValue').textContent = `${rackHeight}U`;
    initRack();
    renderComponents();
}

function resetRack() {
    if (placedComponents.length > 0) {
        if (confirm('Are you sure you want to remove all components from the rack?')) {
            placedComponents = [];
            deselectComponent();
            renderComponents();
        }
    }
}

document.getElementById('increaseHeight').addEventListener('click', () => updateHeight(1));
document.getElementById('decreaseHeight').addEventListener('click', () => updateHeight(-1));

document.querySelectorAll('.component-item').forEach(item => {
    item.addEventListener('dragstart', handleDragStart);
});

document.addEventListener('click', (e) => {
    if (selectedComponentId &&
        !e.target.closest('.placed-component') &&
        !e.target.closest('.details-panel')) {
        deselectComponent();
    }
});

initRack();
document.getElementById('mainArea').classList.add('no-selection');
