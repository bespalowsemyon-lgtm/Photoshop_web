document.addEventListener("DOMContentLoaded", () => {
    // Проверяем, загрузилась ли библиотека Fabric вообще
    if (typeof fabric === 'undefined') {
        alert("Критическая ошибка: Библиотека Fabric.js не загружена! Проверьте наличие файла static/fabric.min.js");
        return;
    }

    // Инициализация холста
    const canvas = new fabric.Canvas('main-canvas', {
        width: 800,
        height: 550,
        backgroundColor: '#111111',
        preserveObjectStacking: true
    });

    let currentFilterType = null;
    const modal = document.getElementById('filter-modal');
    const rangeInput = document.getElementById('filter-range');
    const rangeDisplay = document.getElementById('range-display');

    if (rangeInput && rangeDisplay) {
        rangeInput.oninput = function() { rangeDisplay.innerText = this.value; };
    }

    window.closeModal = function() {
        if (modal) modal.style.display = 'none';
    };

    // === ИНИЦИАЛИЗАЦИЯ БЕЛОГО СЛОЯ-ФОНА ===
    function createBackgroundLayer() {
        const bgRect = new fabric.Rect({
            left: 0,
            top: 0,
            fill: '#ffffff',
            width: canvas.width,
            height: canvas.height,
            selectable: true,
            hasControls: false,
            layerName: 'Задний план (Фон)'
        });

        canvas.add(bgRect);
        canvas.sendToBack(bgRect);
        canvas.renderAll();
    }

    // === ЛОГИКА ДИНАМИЧЕСКИХ СЛОЕВ ===
    function updateLayersPanel() {
        const container = document.getElementById('layers-list');
        if (!container) return;
        container.innerHTML = '';

        const objects = canvas.getObjects().slice().reverse();

        if (objects.length === 0) {
            container.innerHTML = '<small style="color:#666;text-align:center;display:block;padding:10px;">Нет слоев</small>';
            return;
        }

        objects.forEach((obj) => {
            if (!obj.layerName) {
                obj.layerName = obj.type === 'image' ? 'Изображение' : (obj.type === 'i-text' ? 'Текст' : 'Фигура');
            }

            const activeObj = canvas.getActiveObject();
            const isActive = activeObj === obj || (activeObj && activeObj.type === 'activeSelection' && activeObj.contains(obj));

            const layerItem = document.createElement('div');
            layerItem.className = `layer-item ${isActive ? 'active' : ''}`;

            layerItem.onclick = (e) => {
                if (e.target.closest('.layer-btn')) return;
                canvas.setActiveObject(obj);
                canvas.renderAll();
            };

            const objIndex = canvas.getObjects().indexOf(obj);

            layerItem.innerHTML = `
                <div class="layer-info">
                    <span class="layer-name">${obj.layerName}</span>
                </div>
                <div class="layer-controls">
                    <button class="layer-btn ${obj.visible ? '' : 'active'}" title="Видимость" onclick="window.toggleVisibility(${objIndex})">
                        ${obj.visible ? '👁️' : '🕶️'}
                    </button>
                    <button class="layer-btn ${obj.lockMovementX ? 'active' : ''}" title="Заблокировать" onclick="window.toggleLock(${objIndex})">
                        ${obj.lockMovementX ? '🔒' : '🔓'}
                    </button>
                    <button class="layer-btn" title="Выше" onclick="window.moveLayerUp(${objIndex})">▲</button>
                    <button class="layer-btn" title="Ниже" onclick="window.moveLayerDown(${objIndex})">▼</button>
                </div>
            `;
            container.appendChild(layerItem);
        });
    }

    canvas.on('object:added', updateLayersPanel);
    canvas.on('object:removed', updateLayersPanel);
    canvas.on('selection:created', updateLayersPanel);
    canvas.on('selection:updated', updateLayersPanel);
    canvas.on('selection:cleared', updateLayersPanel);

    window.toggleVisibility = function(actualIndex) {
        const obj = canvas.getObjects()[actualIndex];
        if (!obj) return;
        obj.visible = !obj.visible;
        canvas.discardActiveObject();
        canvas.renderAll();
        updateLayersPanel();
    };

    window.toggleLock = function(actualIndex) {
        const obj = canvas.getObjects()[actualIndex];
        if (!obj) return;
        const isLocked = !obj.lockMovementX;
        obj.set({
            lockMovementX: isLocked, lockMovementY: isLocked,
            lockScalingX: isLocked, lockScalingY: isLocked,
            lockRotation: isLocked, hasControls: !isLocked
        });
        canvas.renderAll();
        updateLayersPanel();
    };

    window.moveLayerUp = function(actualIndex) {
        const obj = canvas.getObjects()[actualIndex];
        if (!obj) return;
        canvas.bringForward(obj);
        canvas.renderAll();
        updateLayersPanel();
    };

    window.moveLayerDown = function(actualIndex) {
        const obj = canvas.getObjects()[actualIndex];
        if (!obj) return;
        canvas.sendBackwards(obj);
        canvas.renderAll();
        updateLayersPanel();
    };

    // === ИСПРАВЛЕННОЕ НАДЕЖНОЕ ОТКРЫТИЕ ФАЙЛА ===
    const uploadInput = document.getElementById('upload');
    if (uploadInput) {
        uploadInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = function(f) {
                const imgElement = new Image();
                imgElement.src = f.target.result;

                imgElement.onload = function() {
                    const imgInstance = new fabric.Image(imgElement, {
                        left: 0,
                        top: 0,
                        cornerColor: '#00a8ff',
                        cornerStyle: 'circle',
                        borderColor: '#00a8ff',
                        transparentCorners: false,
                        layerName: `Фото: ${file.name}`
                    });

                    if (imgInstance.width > 600) {
                        imgInstance.scaleToWidth(600);
                    }

                    canvas.add(imgInstance);
                    canvas.centerObject(imgInstance);
                    canvas.setActiveObject(imgInstance);
                    canvas.renderAll();
                };
            };
            reader.readAsDataURL(file);
            this.value = '';
        });
    }

    // === КНОПКИ ДЛЯ ИНСТРУМЕНТОВ ===
    window.applyFilter = function(type) {
        const obj = canvas.getActiveObject();
        if (!obj || obj.type !== 'image') return alert('Выберите слой с картинкой');
        currentFilterType = type;

        if (type === 'blur') {
            const labelText = document.getElementById('label-text');
            if (labelText) labelText.innerText = "Радиус размытия:";
            if (rangeInput) { rangeInput.min = 1; rangeInput.max = 30; rangeInput.value = 5; }
            if (rangeDisplay) rangeDisplay.innerText = "5";
            if (modal) modal.style.display = 'flex';
        } else {
            window.confirmFilter();
        }
    };

    window.confirmFilter = async function() {
        const obj = canvas.getActiveObject();
        const intensity = rangeInput ? rangeInput.value : 5;
        closeModal();

        obj.set('opacity', 0.5);
        canvas.renderAll();

        const blob = await (await fetch(obj.toDataURL())).blob();
        const formData = new FormData();
        formData.append('file', blob);
        formData.append('filter_type', currentFilterType);
        formData.append('intensity', intensity);

        const res = await fetch('/api/filter', { method: 'POST', body: formData });
        const data = await res.json();

        const imgElement = new Image();
        imgElement.src = data.image;
        imgElement.onload = function() {
            const newImg = new fabric.Image(imgElement, {
                left: obj.left, top: obj.top,
                scaleX: obj.scaleX, scaleY: obj.scaleY,
                angle: obj.angle, layerName: obj.layerName,
                cornerColor: '#00a8ff', cornerStyle: 'circle',
                borderColor: '#00a8ff', transparentCorners: false
            });
            canvas.remove(obj);
            canvas.add(newImg);
            canvas.setActiveObject(newImg);
            canvas.renderAll();
        };
    };

    window.addText = function() {
        const text = new fabric.IText('Новый текст', { left: 50, top: 50, fontFamily: 'sans-serif', fill: '#333333' });
        text.layerName = `Текст: "${text.text}"`;
        canvas.add(text);
        canvas.setActiveObject(text);
    };

    window.addRect = function() {
        const rect = new fabric.Rect({ left: 100, top: 100, fill: '#00a8ff', width: 100, height: 100, rx: 5, ry: 5 });
        rect.layerName = `Прямоугольник`;
        canvas.add(rect);
        canvas.setActiveObject(rect);
    };

    window.deleteObject = function() {
        const active = canvas.getActiveObject();
        if (active) canvas.remove(active);
    };

    window.addEventListener('keydown', (e) => {
        if ((e.key === 'Delete' || e.key === 'Backspace') && !canvas.getActiveObject()?.isEditing) {
            window.deleteObject();
        }
    });

    canvas.on('object:moving', updateProperties);
    canvas.on('object:scaling', updateProperties);
    canvas.on('selection:created', updateProperties);
    canvas.on('selection:cleared', () => {
        const props = document.getElementById('obj-properties');
        if (props) props.innerText = 'Выберите объект на холсте';
    });

    function updateProperties() {
        const obj = canvas.getActiveObject();
        const props = document.getElementById('obj-properties');
        if (obj && props) {
            props.innerHTML = `
                Тип: ${obj.type.toUpperCase()}<br>
                X: ${Math.round(obj.left)} | Y: ${Math.round(obj.top)}<br>
                W: ${Math.round(obj.width * obj.scaleX)} | H: ${Math.round(obj.height * obj.scaleY)}
            `;
        }
    }

    const downloadBtn = document.getElementById('download-btn');
    if (downloadBtn) {
        downloadBtn.onclick = () => {
            const link = document.createElement('a');
            link.download = 'photoshop_export.png';
            link.href = canvas.toDataURL({ format: 'png', quality: 1, multiplier: 2 });
            link.click();
        };
    }

    // Запускаем создание фона
    createBackgroundLayer();
});