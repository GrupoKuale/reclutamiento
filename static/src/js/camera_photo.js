/** @odoo-module **/

import { onMounted } from "@odoo/owl";
import { FormController } from "@web/views/form/form_controller";
import { patch } from "@web/core/utils/patch";

patch(FormController.prototype, {
    setup() {
        super.setup(...arguments);
        onMounted(() => {
            if (this.props.resModel === 'hr.applicant') {
                this._initCameraBtn();
            }
        });
    },

    _initCameraBtn() {
        setTimeout(() => {
            const photoField = document.querySelector('[name="applicant_photo"]');
            if (!photoField) return;
            const imageWrapper = photoField.querySelector('.opacity-trigger-hover');
            if (!imageWrapper || document.getElementById('btn_open_camera')) return;

            const actionDiv = imageWrapper.querySelector('.position-absolute');
            const target = actionDiv || imageWrapper;

            /* ── Botón cámara ── */
            const btn = document.createElement('span');
            btn.id = 'btn_open_camera';
            btn.className = 'btn btn-light border-0 rounded-circle m-1 p-1';
            btn.setAttribute('title', 'Tomar foto');
            btn.innerHTML = '<i class="fa fa-camera fa-fw"></i>';
            btn.style.display = 'none';
            target.appendChild(btn);
            imageWrapper.addEventListener('mouseenter', () => { btn.style.display = 'inline-block'; });
            imageWrapper.addEventListener('mouseleave', () => { btn.style.display = 'none'; });

            const getEl = id => document.getElementById(id);

            /* ── Estado ── */
            let faceOk         = false;
            let ovalAnimFrame  = null;
            let ovalPhase      = 0;
            let detectInterval = null;
            let countdownTimer = null;
            let countdownVal   = 0;
            let countingDown   = false;   // true mientras corre el countdown

            const analyzeCanvas = document.createElement('canvas');
            const analyzeCtx    = analyzeCanvas.getContext('2d');

            /* ── Detección de piel YCbCr ── */
            const isSkinPixel = (r, g, b) => {
                const cb = -0.169 * r - 0.331 * g + 0.500 * b + 128;
                const cr =  0.500 * r - 0.419 * g - 0.081 * b + 128;
                const y  =  0.299 * r + 0.587 * g + 0.114 * b;
                return (y > 80) && (cb >= 77 && cb <= 127) && (cr >= 133 && cr <= 173);
            };

            const detectFaceInVideo = (video) => {
                const vw = video.videoWidth;
                const vh = video.videoHeight;
                if (!vw || !vh || video.readyState < 2) return null;
                const SCALE = 0.15;
                const sw = Math.round(vw * SCALE);
                const sh = Math.round(vh * SCALE);
                analyzeCanvas.width  = sw;
                analyzeCanvas.height = sh;
                analyzeCtx.drawImage(video, 0, 0, sw, sh);
                const { data } = analyzeCtx.getImageData(0, 0, sw, sh);
                const CELL = 4;
                const cols = Math.floor(sw / CELL);
                const rows = Math.floor(sh / CELL);
                const skinMap = new Uint8Array(cols * rows);
                for (let row = 0; row < rows; row++) {
                    for (let col = 0; col < cols; col++) {
                        let skinCount = 0, total = 0;
                        for (let dy = 0; dy < CELL; dy++) {
                            for (let dx = 0; dx < CELL; dx++) {
                                const px = (row * CELL + dy) * sw + (col * CELL + dx);
                                const i  = px * 4;
                                if (i + 2 < data.length) {
                                    if (isSkinPixel(data[i], data[i+1], data[i+2])) skinCount++;
                                    total++;
                                }
                            }
                        }
                        skinMap[row * cols + col] = (skinCount / total) >= 0.45 ? 1 : 0;
                    }
                }
                const visited = new Uint8Array(cols * rows);
                let bestBlob = null, bestSize = 0;
                for (let startRow = 0; startRow < rows; startRow++) {
                    for (let startCol = 0; startCol < cols; startCol++) {
                        const idx = startRow * cols + startCol;
                        if (!skinMap[idx] || visited[idx]) continue;
                        const queue = [idx];
                        visited[idx] = 1;
                        let minR = startRow, maxR = startRow, minC = startCol, maxC = startCol, size = 0;
                        while (queue.length) {
                            const cur = queue.pop();
                            const r = Math.floor(cur / cols), c = cur % cols;
                            size++;
                            if (r < minR) minR = r; if (r > maxR) maxR = r;
                            if (c < minC) minC = c; if (c > maxC) maxC = c;
                            for (const n of [cur-cols, cur+cols, cur-1, cur+1,
                                             cur-cols-1, cur-cols+1, cur+cols-1, cur+cols+1]) {
                                if (n >= 0 && n < skinMap.length && skinMap[n] && !visited[n]) {
                                    visited[n] = 1; queue.push(n);
                                }
                            }
                        }
                        if (size > bestSize) { bestSize = size; bestBlob = { minR, maxR, minC, maxC, size }; }
                    }
                }
                if (!bestBlob || bestBlob.size < 20) return null;
                const bx = bestBlob.minC * CELL / SCALE;
                const by = bestBlob.minR * CELL / SCALE;
                const bw = (bestBlob.maxC - bestBlob.minC + 1) * CELL / SCALE;
                const bh = (bestBlob.maxR - bestBlob.minR + 1) * CELL / SCALE;
                if (bh / bw < 0.8 || bh / bw > 3.0 || bw < vw * 0.10) return null;
                return { x: bx, y: by, width: bw, height: bh };
            };

            /* ── UI del óvalo y botón ── */
            const setOvalState = (state) => {
                const oval   = getEl('face_oval');
                const dot    = getEl('camera_status_dot');
                const hint   = getEl('camera_hint');
                const btnCap = getEl('camera_capture');
                if (!oval) return;
                if (state === 'ok') {
                    oval.setAttribute('stroke', '#22c55e');
                    oval.setAttribute('stroke-width', '3.5');
                    oval.setAttribute('stroke-dasharray', '0');
                    if (dot) dot.setAttribute('fill', '#22c55e');
                    if (hint) { hint.textContent = '¡Listo! Presiona Capturar'; hint.style.color = '#16a34a'; }
                    if (btnCap) {
                        btnCap.style.background  = '#16a34a';
                        btnCap.style.boxShadow   = '0 0 0 5px rgba(34,197,94,.35)';
                        btnCap.style.cursor      = 'pointer';
                        btnCap.style.pointerEvents = 'auto';
                        btnCap.style.opacity     = '1';
                    }
                } else if (state === 'bad') {
                    oval.setAttribute('stroke', '#ef4444');
                    oval.setAttribute('stroke-width', '2.5');
                    oval.setAttribute('stroke-dasharray', '8 4');
                    if (dot) dot.setAttribute('fill', '#ef4444');
                    if (hint) hint.style.color = '#dc2626';
                    if (btnCap && !countingDown) {
                        btnCap.style.background    = '#9ca3af';
                        btnCap.style.boxShadow     = 'none';
                        btnCap.style.cursor        = 'not-allowed';
                        btnCap.style.pointerEvents = 'none';
                        btnCap.style.opacity       = '0.6';
                    }
                } else { // neutral
                    oval.setAttribute('stroke', '#ffffff');
                    oval.setAttribute('stroke-width', '2.5');
                    oval.setAttribute('stroke-dasharray', '8 4');
                    if (dot) dot.setAttribute('fill', '#9ca3af');
                    if (hint) { hint.textContent = 'Coloca tu rostro dentro del óvalo'; hint.style.color = '#6c757d'; }
                    if (btnCap) {
                        btnCap.style.background    = '#9ca3af';
                        btnCap.style.boxShadow     = 'none';
                        btnCap.style.cursor        = 'not-allowed';
                        btnCap.style.pointerEvents = 'none';
                        btnCap.style.opacity       = '0.6';
                    }
                }
            };

            /* ── Animación pulso ── */
            const animateOval = () => {
                const oval = getEl('face_oval');
                if (!oval) return;
                ovalPhase += 0.05;
                if (faceOk) {
                    const s = 1 + Math.sin(ovalPhase) * 0.022;
                    oval.setAttribute('transform', `translate(204,108) scale(${s}) translate(-204,-108)`);
                } else {
                    oval.removeAttribute('transform');
                }
                ovalAnimFrame = requestAnimationFrame(animateOval);
            };

            /* ── Cancelar countdown si la cara se mueve ── */
            const cancelCountdown = () => {
                if (countdownTimer) { clearTimeout(countdownTimer); countdownTimer = null; }
                countingDown = false;
                const hint = getEl('camera_hint');
                if (hint && faceOk) { hint.textContent = '¡Listo! Presiona Capturar'; hint.style.color = '#16a34a'; }
            };

            /* ── Countdown → captura (solo arranca desde el botón) ── */
            const startCountdown = () => {
                if (countingDown) return;
                if (!faceOk) return;               // No iniciar si la cara no está OK
                countingDown = true;
                countdownVal = 3;
                const hint   = getEl('camera_hint');
                const tick = () => {
                    // Si la cara se movió durante el countdown → cancelar
                    if (!faceOk) {
                        countingDown = false;
                        clearTimeout(countdownTimer);
                        countdownTimer = null;
                        setOvalState('bad');
                        if (hint) hint.textContent = 'Centra tu rostro en el óvalo';
                        return;
                    }
                    if (hint) hint.textContent = `Capturando en ${countdownVal}…`;
                    if (countdownVal <= 0) {
                        countdownTimer  = null;
                        countingDown    = false;
                        capturePhoto();
                        return;
                    }
                    countdownVal--;
                    countdownTimer = setTimeout(tick, 1000);
                };
                tick();
            };

            /* ── Evaluar posición ── */
            const evaluateFace = (video, box) => {
                if (countingDown) return;  // No interrumpir un countdown activo
                const vw = video.videoWidth, vh = video.videoHeight;
                const oCX = vw * 0.50, oCY = vh * 0.415;
                const oRX = vw * 0.195, oRY = vh * 0.370;
                const fcx = box.x + box.width / 2, fcy = box.y + box.height / 2;
                const dx = (fcx - oCX) / oRX, dy = (fcy - oCY) / oRY;
                const inOval = (dx * dx + dy * dy) <= 1.05;
                const ratio  = box.width / vw;
                const sizeOk = ratio >= 0.18 && ratio <= 0.72;
                const hint   = getEl('camera_hint');
                if (inOval && sizeOk) {
                    if (!faceOk) { faceOk = true; setOvalState('ok'); }
                } else {
                    if (faceOk) { faceOk = false; }
                    setOvalState('bad');
                    if (hint) {
                        if (ratio < 0.18)      hint.textContent = 'Acércate un poco más';
                        else if (ratio > 0.72) hint.textContent = 'Aléjate un poco';
                        else                   hint.textContent = 'Centra tu rostro en el óvalo';
                    }
                }
            };

            const startDetection = (video) => {
                if (detectInterval) clearInterval(detectInterval);
                detectInterval = setInterval(() => {
                    const box = detectFaceInVideo(video);
                    if (box) {
                        evaluateFace(video, box);
                    } else {
                        if (!countingDown) {
                            if (faceOk) { faceOk = false; }
                            setOvalState('bad');
                            const hint = getEl('camera_hint');
                            if (hint) hint.textContent = 'No se detecta tu rostro';
                        }
                    }
                }, 200);
            };

            /* ── Zoom ── */
            const applyZoom = (video, level) => {
                const stream = video.srcObject;
                if (stream) {
                    const track = stream.getVideoTracks()[0];
                    if (track) {
                        const caps = track.getCapabilities ? track.getCapabilities() : {};
                        if (caps.zoom) {
                            const zv = caps.zoom.min + (caps.zoom.max - caps.zoom.min) * ((level - 1) / 2);
                            track.applyConstraints({ advanced: [{ zoom: zv }] }).catch(() => {});
                            return;
                        }
                    }
                }
                video.style.transform = `scale(${level})`;
            };

            /* ── Captura cuadrada 600×600 recortando zona del óvalo ── */
            const capturePhoto = () => {
                const video  = getEl('camera_video');
                const canvas = getEl('camera_canvas');
                if (!video || !canvas) return;
                const vw = video.videoWidth, vh = video.videoHeight;
                const svgW = 408, svgH = 260;
                const scaleX = vw / svgW, scaleY = vh / svgH;
                const cropSvgX = 88, cropSvgY = 15, cropSvgW = 232, cropSvgH = 245;
                let cropX = Math.round(cropSvgX * scaleX);
                let cropY = Math.round(cropSvgY * scaleY);
                let cropW = Math.round(cropSvgW * scaleX);
                let cropH = Math.round(cropSvgH * scaleY);
                const side = Math.max(cropW, cropH);
                cropX = Math.round(vw / 2 - side / 2);
                cropW = side; cropH = side;
                const zoomLevel = parseFloat((getEl('camera_zoom') || {}).value || 100) / 100;
                if (zoomLevel > 1) {
                    const zw = vw / zoomLevel, zh = vh / zoomLevel;
                    const offX = (vw - zw) / 2, offY = (vh - zh) / 2;
                    cropX = Math.round(offX + cropX / zoomLevel);
                    cropY = Math.round(offY + cropY / zoomLevel);
                    cropW = Math.round(cropW / zoomLevel);
                    cropH = Math.round(cropH / zoomLevel);
                }
                cropX = Math.max(0, Math.min(cropX, vw - 10));
                cropY = Math.max(0, Math.min(cropY, vh - 10));
                cropW = Math.min(cropW, vw - cropX);
                cropH = Math.min(cropH, vh - cropY);
                const OUTPUT_SIZE = 600;
                canvas.width  = OUTPUT_SIZE;
                canvas.height = OUTPUT_SIZE;
                const ctx = canvas.getContext('2d');
                ctx.fillStyle = '#ffffff';
                ctx.fillRect(0, 0, OUTPUT_SIZE, OUTPUT_SIZE);
                ctx.drawImage(video, cropX, cropY, cropW, cropH, 0, 0, OUTPUT_SIZE, OUTPUT_SIZE);
                canvas.toBlob(blob => {
                    const file = new File([blob], 'foto_candidato.jpg', { type: 'image/jpeg' });
                    const dt = new DataTransfer();
                    dt.items.add(file);
                    const fieldEl   = document.querySelector('[name="applicant_photo"]');
                    const inputFile = fieldEl ? fieldEl.querySelector('input[type="file"]') : null;
                    if (inputFile) {
                        inputFile.files = dt.files;
                        // Disparar todos los eventos que Odoo escucha para detectar cambio
                        ['change', 'input'].forEach(evName => {
                            inputFile.dispatchEvent(new Event(evName, { bubbles: true }));
                        });
                        // Esperar a que Odoo procese el campo y luego guardar automáticamente
                        setTimeout(() => {
                            // Método 1: usar el propio método save del FormController (más confiable)
                            try {
                                if (this.model && this.model.root) {
                                    this.model.root.save({ stayInEdition: true }).catch(() => {});
                                    return;
                                }
                            } catch(e) {}
                            // Método 2: click en el botón guardar de Odoo
                            const saveBtn = document.querySelector('.o_form_button_save') ||
                                            document.querySelector('[data-hotkey="s"].btn-primary') ||
                                            document.querySelector('.o_form_status_indicator_buttons .btn-primary');
                            if (saveBtn) {
                                saveBtn.click();
                            }
                        }, 800);
                    }
                }, 'image/jpeg', 0.95);
                closeCamera();
            };

            /* ── Cerrar ── */
            const closeCamera = () => {
                if (ovalAnimFrame)  { cancelAnimationFrame(ovalAnimFrame); ovalAnimFrame = null; }
                if (detectInterval) { clearInterval(detectInterval); detectInterval = null; }
                if (countdownTimer) { clearTimeout(countdownTimer); countdownTimer = null; }
                countingDown = false;
                faceOk = false;
                if (this._cameraStream) {
                    this._cameraStream.getTracks().forEach(t => t.stop());
                    this._cameraStream = null;
                }
                const video = getEl('camera_video');
                if (video) { video.srcObject = null; video.style.transform = 'scale(1)'; }
                const modal = getEl('camera_modal');
                if (modal) modal.style.display = 'none';
                setOvalState('neutral');
            };

            /* ── Abrir cámara ── */
            btn.addEventListener('click', () => {
                const modal = getEl('camera_modal');
                if (!modal) return;
                modal.style.display = 'flex';
                faceOk = false;
                countingDown = false;
                ovalPhase = 0;
                const zoomSlider = getEl('camera_zoom');
                const zoomLabel  = getEl('camera_zoom_label');
                if (zoomSlider) zoomSlider.value = 100;
                if (zoomLabel)  zoomLabel.textContent = '1.0×';
                setOvalState('neutral');
                navigator.mediaDevices.getUserMedia({
                    video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 720 } },
                    audio: false
                })
                .then(stream => {
                    this._cameraStream = stream;
                    const video = getEl('camera_video');
                    video.srcObject = stream;
                    video.style.transform = 'scale(1)';
                    animateOval();
                    video.addEventListener('loadeddata', () => startDetection(video), { once: true });
                    if (zoomSlider) {
                        zoomSlider.oninput = () => {
                            const level = zoomSlider.value / 100;
                            if (zoomLabel) zoomLabel.textContent = level.toFixed(1) + '×';
                            applyZoom(video, level);
                        };
                    }
                })
                .catch(err => {
                    alert('No se pudo acceder a la cámara: ' + err.message);
                    modal.style.display = 'none';
                });
            });

            /* ── Listeners ── */
            const btnClose   = getEl('camera_close');
            const btnCapture = getEl('camera_capture');
            const modal      = getEl('camera_modal');
            if (btnClose) btnClose.addEventListener('click', closeCamera);
            if (btnCapture) {
                btnCapture.addEventListener('click', () => {
                    if (faceOk && !countingDown) startCountdown();
                });
            }
            if (modal) modal.addEventListener('click', e => { if (e.target === modal) closeCamera(); });

        }, 800);
    }
});