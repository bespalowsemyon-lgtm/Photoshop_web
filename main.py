import uvicorn
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from PIL import Image, ImageOps, ImageFilter
import io
import base64

app = FastAPI()


@app.post("/api/filter")
async def apply_filter(
        file: UploadFile = File(...),
        filter_type: str = Form(...),
        intensity: int = Form(5)
):
    contents = await file.read()
    image = Image.open(io.BytesIO(contents)).convert("RGBA")

    if filter_type == "grayscale":
        image = ImageOps.grayscale(image).convert("RGBA")
    elif filter_type == "blur":
        image = image.filter(ImageFilter.GaussianBlur(radius=intensity))
    elif filter_type == "invert":
        r, g, b, a = image.split()
        rgb_image = Image.merge('RGB', (r, g, b))
        inverted_image = ImageOps.invert(rgb_image)
        r2, g2, b2 = inverted_image.split()
        image = Image.merge('RGBA', (r2, g2, b2, a))

    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    return {"image": f"data:image/png;base64,{img_str}"}


@app.get("/", response_class=HTMLResponse)
async def read_index():
    # Возвращаем абсолютно всё внутри одной HTML строки напрямую из памяти сервера
    return """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PyPhotoshop Monolith Edition</title>
    <!-- Подключаем официальный стабильный CDN Fabric.js -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/fabric.js/5.3.1/fabric.min.js"></script>
    <style>
        :root {
            --bg-app: #1e1e1e;
            --bg-side: #333333;
            --bg-header: #3c3c3c;
            --accent: #00a8ff;
            --accent-hover: #0097e6;
            --text-main: #d5d5d5;
            --border-dark: #1a1a1a;
            --selection: #4b4b4b;
        }

        body, html {
            margin: 0; padding: 0; height: 100%;
            background-color: var(--bg-app);
            color: var(--text-main);
            font-family: 'Inter', -apple-system, sans-serif;
            font-size: 13px;
            overflow: hidden;
        }

        .app-container { display: flex; flex-direction: column; height: 100vh; }

        .top-bar {
            background: var(--bg-header);
            height: 40px;
            display: flex; align-items: center; justify-content: space-between;
            padding: 0 12px;
            border-bottom: 1px solid var(--border-dark);
            z-index: 10;
        }

        .logo { 
            background: var(--accent); color: #000; font-weight: 900;
            width: 24px; height: 24px; display: flex; align-items: center; justify-content: center;
            border-radius: 3px; margin-right: 15px;
        }

        .main-workspace { display: flex; flex: 1; overflow: hidden; }

        .toolbar {
            width: 36px; background: var(--bg-side);
            display: flex; flex-direction: column; align-items: center;
            padding: 8px 0; border-right: 1px solid var(--border-dark);
        }

        .tool {
            width: 28px; height: 28px; margin-bottom: 4px;
            display: flex; align-items: center; justify-content: center;
            cursor: pointer; border-radius: 2px; font-size: 14px;
        }
        .tool:hover { background: var(--selection); }

        .canvas-area {
            flex: 1; background: #111;
            background-image: radial-gradient(#222 1px, transparent 1px);
            background-size: 20px 20px;
            display: flex; align-items: center; justify-content: center; overflow: auto;
        }

        .canvas-wrapper { box-shadow: 0 10px 40px rgba(0,0,0,0.8); border: 1px solid #000; }

        .side-panel {
            width: 260px; background: var(--bg-side);
            border-left: 1px solid var(--border-dark); display: flex; flex-direction: column;
        }

        .panel-section { border-bottom: 1px solid var(--border-dark); padding: 12px; }
        .panel-title { text-transform: uppercase; font-size: 10px; font-weight: bold; color: #888; margin-bottom: 10px; letter-spacing: 1px; }

        .layers-container {
            flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 4px;
        }

        .layer-item {
            background: #2a2a2a; padding: 6px 10px; border-radius: 4px;
            display: flex; align-items: center; justify-content: space-between;
            border: 1px solid transparent; cursor: pointer; user-select: none;
        }
        .layer-item:hover { background: #383838; }
        .layer-item.active { background: var(--selection); border-color: var(--accent); }

        .layer-info { display: flex; align-items: center; gap: 8px; flex: 1; min-width: 0; }
        .layer-name { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-size: 12px; }

        .layer-controls { display: flex; gap: 4px; }
        .layer-btn {
            background: none; border: none; color: #888; padding: 2px;
            cursor: pointer; font-size: 11px; border-radius: 2px;
        }
        .layer-btn:hover { color: #fff; background: #444; }
        .layer-btn.active { color: var(--accent); }

        .modal-overlay {
            display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.7); z-index: 1000; align-items: center; justify-content: center;
        }
        .modal-content { background: var(--bg-side); width: 300px; border-radius: 6px; border: 1px solid var(--border-dark); box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
        .modal-header { padding: 10px 15px; border-bottom: 1px solid var(--border-dark); display: flex; justify-content: space-between; align-items: center; }
        .modal-body { padding: 20px 15px; }
        .modal-footer { padding: 10px 15px; border-top: 1px solid var(--border-dark); display: flex; justify-content: flex-end; gap: 10px; }

        input[type="range"] { width: 100%; margin-top: 10px; accent-color: var(--accent); }
        .close-btn { background: none; border: none; font-size: 20px; cursor: pointer; color: #888; }
        button { background: #444; color: #eee; border: 1px solid #555; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 12px; }
        button:hover { background: #555; }
        .btn-primary { background: var(--accent); color: white; border: none; font-weight: 600; }
        .btn-primary:hover { background: var(--accent-hover); }
    </style>
</head>
<body>
    <div class="app-container">
        <header class="top-bar">
            <div style="display: flex; align-items: center;">
                <div class="logo">Ps</div>
                <button onclick="document.getElementById('upload').click()">Открыть файл</button>
                <input type="file" id="upload" hidden accept="image/*">
                <div style="margin-left: 10px; display: flex; gap: 5px;">
                    <button onclick="applyFilter('grayscale')">ЧБ</button>
                    <button onclick="applyFilter('blur')">Размытие</button>
                    <button onclick="applyFilter('invert')">Инверсия</button>
                </div>
            </div>
            <button class="btn-primary" id="download-btn">Экспорт PNG</button>
        </header>

        <div class="main-workspace">
            <aside class="toolbar">
                <div class="tool active" title="Перемещение">🔍</div>
                <div class="tool" onclick="addText()" title="Текст">T</div>
                <div class="tool" onclick="addRect()" title="Фигура">⬜</div>
                <div style="margin-top: auto;" class="tool" onclick="deleteObject()" title="Удалить">🗑️</div>
            </aside>

            <main class="canvas-area">
                <div class="canvas-wrapper">
                    <canvas id="main-canvas" width="800" height="550"></canvas>
                </div>
            </main>

            <aside class="side-panel">
                <div class="panel-section">
                    <div class="panel-title">Свойства объекта</div>
                    <div id="obj-properties" style="font-size: 11px; color: #aaa;">
                        Выберите объект на холсте
                    </div>
                </div>
                <div class="panel-section" style="flex: 1; display: flex; flex-direction: column;">
                    <div class="panel-title">Слои</div>
                    <div id="layers-list" class="layers-container"></div>
                </div>
            </aside>
        </div>
    </div>

    <div id="filter-modal" class="modal-overlay">
        <div class="modal-content">
            <div class="modal-header">
                <span id="modal-title">Настройки фильтра</span>
                <button class="close-btn" onclick="closeModal()">&times;</button>
            </div>
            <div class="modal-body">
                <label for="filter-range" id="label-text">Интенсивность:</label>
                <input type="range" id="filter-range" min="1" max="20" value="5">
                <span id="range-display">5</span>
            </div>
            <div class="modal-footer">
                <button onclick="closeModal()">Отмена</button>
                <button class="btn-primary" onclick="confirmFilter()">Применить</button>
            </div>
        </div>
    </div>

    <script>
        document.addEventListener("DOMContentLoaded", () => {
            if (typeof fabric === 'undefined') {
                alert("Критическая ошибка: Браузер заблокировал загрузку Fabric.js! Проверь подключение к сети.");
                return;
            }

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

            // === ОТКРЫТИЕ ФАЙЛА НАПРЯМУЮ ===
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

            // === УПРАВЛЕНИЕ ИНСТРУМЕНТАМИ ===
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
                const text = new fabric.IText('Новый текст', { left: 100, top: 100, fontFamily: 'sans-serif', fill: '#333333' });
                text.layerName = `Текст: "${text.text}"`;
                canvas.add(text);
                canvas.setActiveObject(text);
                canvas.renderAll();
            };

            window.addRect = function() {
                const rect = new fabric.Rect({ left: 150, top: 150, fill: '#00a8ff', width: 120, height: 120, rx: 5, ry: 5 });
                rect.layerName = `Прямоугольник`;
                canvas.add(rect);
                canvas.setActiveObject(rect);
                canvas.renderAll();
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

            // Запускаем белый холст-слой
            createBackgroundLayer();
        });
    </script>
</body>
</html>
"""


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)