/** @odoo-module **/

import { registry } from "@web/core/registry";

const actionRegistry = registry.category("actions");

// ── Helpers DOM ─────────────────────────────────────────────────────────────
function _el(id) { return document.getElementById(id); }

// ── Timer circular ───────────────────────────────────────────────────────────
const TIMER_TOTAL  = 135;   // 45 intentos × 3s
const TIMER_CIRCUM = 100.5; // 2π×16
let _timerSec      = TIMER_TOTAL;
let _timerInterval = null;

function _timerStart() {
    _timerStop();
    _timerSec = TIMER_TOTAL;
    _timerRender(_timerSec);
    _timerInterval = setInterval(() => {
        _timerSec--;
        _timerRender(_timerSec);
        if (_timerSec <= 0) _timerStop();
    }, 1000);
}

function _timerStop() {
    if (_timerInterval) { clearInterval(_timerInterval); _timerInterval = null; }
}

function _timerRender(sec) {
    const arc   = _el('zk_timer_arc');
    const label = _el('zk_timer_label');
    if (!arc || !label) return;

    const offset = TIMER_CIRCUM * (1 - sec / TIMER_TOTAL);
    arc.style.strokeDashoffset = offset;

    const m = Math.floor(sec / 60);
    const s = sec % 60;
    label.textContent = `${m}:${s < 10 ? '0' : ''}${s}`;

    // SVG requiere setAttribute para class
    const colorClass = sec <= 20 ? 'danger' : sec <= 45 ? 'warn' : '';
    arc.setAttribute('class', 'zk-timer-arc' + (colorClass ? ' ' + colorClass : ''));
    label.className = 'zk-timer-label' + (colorClass ? ' ' + colorClass : '');
}

// ── Estado visual ────────────────────────────────────────────────────────────
let _activeInterval = null;

function setZkState(state, customText, customHint) {
    const area        = _el('zk_scanner_area');
    const statusBadge = _el('zk_status_badge');
    const statusText  = _el('zk_status_text');
    const instruction = _el('zk_instruction');
    const fingerFill  = _el('zk_finger_fill');

    if (!area) return;

    const STATES = {
        idle:     { text: 'Listo para registrar',      hint: 'Presiona "Registrar" para activar el reloj checador', fill: '#6366f1' },
        waiting:  { text: 'Esperando huella…',          hint: 'Coloca el dedo en el sensor del reloj checador',      fill: '#6366f1' },
        success:  { text: '¡Huella detectada!',         hint: 'Presiona "Verificar captura" para confirmar',         fill: '#22c55e' },
        enrolled: { text: 'Huella ya registrada',       hint: 'Este postulante ya tiene una huella en el sistema.',  fill: '#22c55e' },
        error:    { text: 'Error',                      hint: 'Revisa la configuración e intenta de nuevo',          fill: '#ef4444' },
    };

    const cfg = STATES[state] || STATES.idle;

    area.className        = `zk-scanner-area state-${state === 'enrolled' ? 'success' : state}`;
    statusBadge.className = `zk-status-badge ${state === 'enrolled' ? 'success' : state}`;
    if (statusText)  statusText.textContent  = customText || cfg.text;
    if (instruction) instruction.textContent = customHint || cfg.hint;

    if (fingerFill) {
        fingerFill.style.transition = 'fill 0.4s ease, opacity 0.4s ease';
        fingerFill.setAttribute('fill', cfg.fill);
        fingerFill.style.opacity = state === 'waiting' ? '0.15' : '0.45';
    }

    if (state === 'waiting') {
        _timerStart();
    } else {
        _timerStop();
    }
}

// ── Manejo de errores ────────────────────────────────────────────────────────
function _handleZkError(msg, notification) {
    const m = msg || '';

    if (_activeInterval) { clearInterval(_activeInterval); _activeInterval = null; }

    if (m.includes('No se pudo conectar') || m.includes('no disponible') || m.includes('timed out')) {
        setZkState('error', 'Sin conexión', 'Reloj no disponible. Verifica que esté encendido y en la red.');
        if (notification) notification.add(m || 'Reloj no disponible.', { type: 'danger', sticky: true });

    } else if (m.includes('ya tiene una huella') || m.includes('duplicada') || m.includes('ya registrada')) {
        setZkState('error', 'Huella duplicada', 'Este usuario ya tiene una huella en ese dedo. Elimínala primero.');
        if (notification) notification.add(m, { type: 'danger', sticky: true });

    } else if (m.includes('UID') && (m.includes('uso') || m.includes('ocupado'))) {
        setZkState('error', 'UID duplicado', 'El UID ya está en uso. Cambia el UID e intenta de nuevo.');
        if (notification) notification.add(m, { type: 'danger', sticky: true });

    } else {
        setZkState('error', 'Error', m || 'Error desconocido. Intenta de nuevo.');
        if (notification && m) notification.add(m, { type: 'danger', sticky: true });
    }
}

// ── Modal de tiempo agotado ──────────────────────────────────────────────────
function _showTimeoutModal() {
    const overlay = document.createElement('div');
    overlay.style.cssText = `
        position:fixed; inset:0; z-index:999999;
        background:rgba(0,0,0,.55);
        display:flex; align-items:center; justify-content:center;
    `;
    overlay.innerHTML = `
        <div style="background:#fff; border-radius:14px; padding:32px 28px;
                    max-width:380px; width:90%;
                    font-family:inherit; text-align:center;">
            <div style="width:48px;height:48px;border-radius:50%;background:#fee2e2;
                        display:flex;align-items:center;justify-content:center;
                        margin:0 auto 14px;font-size:22px;">&#x23F1;</div>
            <h4 style="font-size:16px;font-weight:600;color:#111;margin:0 0 8px;">
                Tiempo agotado
            </h4>
            <p style="font-size:13px;color:#555;line-height:1.6;margin:0 0 22px;">
                No se detectó la huella en el tiempo esperado.<br/>
                Cierra este diálogo y vuelve a intentarlo.
            </p>
            <button id="zk_timeout_close"
                style="background:#6366f1;color:#fff;border:none;border-radius:999px;
                       padding:11px 28px;font-size:13px;font-weight:600;
                       cursor:pointer;width:100%;">
                Cerrar y reintentar
            </button>
        </div>
    `;
    document.body.appendChild(overlay);
    overlay.querySelector('#zk_timeout_close').addEventListener('click', () => {
        document.body.removeChild(overlay);
        const btnCancel = document.querySelector('.zk-enroll-wrapper')
            ?.closest('.modal, .o_dialog')
            ?.querySelector('[special="cancel"], .o_form_button_cancel, button[data-dismiss]');
        if (btnCancel) btnCancel.click();
        setZkState('idle');
    });
}

// ── Action: zk_start_polling ─────────────────────────────────────────────────
function zkStartPolling(env, action) {
    const recordId = action.params?.record_id;

    if (_activeInterval) { clearInterval(_activeInterval); _activeInterval = null; }

    setZkState('waiting');

    let running  = false;
    let attempts = 0;
    const MAX_ATTEMPTS = 45;

    _activeInterval = setInterval(async () => {
        if (running) return;
        running = true;
        attempts++;

        if (attempts > MAX_ATTEMPTS) {
            clearInterval(_activeInterval);
            _activeInterval = null;
            setZkState('error', 'Tiempo agotado', '');
            _showTimeoutModal();
            running = false;
            return;
        }

        try {
            const result = await env.services.orm.call(
                'zk.biometric.create.user.wizard',
                'action_check_enrollment',
                [[recordId]]
            );

            if (result?.done) {
                clearInterval(_activeInterval);
                _activeInterval = null;
                setZkState('success');
                env.services.notification.add(
                    "¡Huella registrada! Presiona 'Verificar captura'.",
                    { type: 'success' }
                );
            }

        } catch (err) {
            const msg = err?.data?.message || err?.message || '';
            _handleZkError(msg, env.services.notification);
        }

        running = false;
    }, 3000);
}

actionRegistry.add('zk_start_polling', zkStartPolling);

// ── Action: zk_enrollment_error ──────────────────────────────────────────────
function zkEnrollmentError(env, action) {
    const msg = action.params?.error || 'Error desconocido al registrar la huella.';
    _handleZkError(msg, env.services.notification);
}

actionRegistry.add('zk_enrollment_error', zkEnrollmentError);

// ── Listeners del modal ───────────────────────────────────────────────────────
function _initModalObserver() {
    const observer = new MutationObserver(() => {
        const wrapper = document.querySelector('.zk-enroll-wrapper');
        if (!wrapper || wrapper.dataset.zkBound) return;
        wrapper.dataset.zkBound = '1';

        const btnReg = document.querySelector('.zk-btn-registrar');
        const btnVer = document.querySelector('.zk-btn-verificar');

        // Leer already_enrolled del checkbox
        const enrolledInput = document.querySelector('[name="already_enrolled"] input[type="checkbox"]');
        const isEnrolled = enrolledInput?.checked === true;

        if (isEnrolled) {
            setZkState('enrolled', 'Huella ya registrada',
                       'Este postulante ya tiene una huella registrada en el sistema.');
        }

        // ── Click en Registrar ──
        if (btnReg) {
            btnReg.addEventListener('click', () => {
                if (btnReg.disabled) return;
                setZkState('waiting', 'Conectando al reloj…', 'Validando configuración, un momento…');
            });
        }

        // ── Click en Verificar captura ──
        if (btnVer) {
            btnVer.addEventListener('click', () => {
                const area = _el('zk_scanner_area');
                if (area?.classList.contains('state-waiting') ||
                    area?.classList.contains('state-success')) {
                    const ins = _el('zk_instruction');
                    const txt = _el('zk_status_text');
                    if (ins) ins.textContent = 'Pon el dedo en el reloj para verificar…';
                    if (txt) txt.textContent = 'Verificando…';
                }
            });
        }
    });

    observer.observe(document.body, { childList: true, subtree: true });
}

if (document.body) {
    _initModalObserver();
} else {
    document.addEventListener('DOMContentLoaded', _initModalObserver);
}

function zkStartVerifyPolling(env, action) {
    const recordId = action.params?.record_id;

    if (_activeInterval) { clearInterval(_activeInterval); _activeInterval = null; }

    // Abrir el modal de verificación
    env.services.action.doAction({
        type:      'ir.actions.act_window',
        name:      'Verificar Huella',
        res_model: 'zk.biometric.verify.wizard',
        views:     [[false, 'form']],   
        view_mode: 'form',
        target:    'new',
        res_id:    recordId,
    }).then(() => {
        _timerStart();

        let running  = false;
        let attempts = 0;
        const MAX_ATTEMPTS = 45;

        _activeInterval = setInterval(async () => {
            if (running) return;
            running = true;
            attempts++;

            if (attempts > MAX_ATTEMPTS) {
                clearInterval(_activeInterval);
                _activeInterval = null;
                setZkState('error', 'Tiempo agotado', '');
                _showTimeoutModal();
                running = false;
                return;
            }

            try {
                const result = await env.services.orm.call(
                    'zk.biometric.verify.wizard',
                    'action_check_verification',
                    [[recordId]]
                );

                if (result?.done) {
                    clearInterval(_activeInterval);
                    _activeInterval = null;
                    setZkState('success', '¡Verificación exitosa!', 'Huella reconocida correctamente.');

                    setTimeout(async () => {
                        const btnCancel = document.querySelector('.zk-enroll-wrapper')
                            ?.closest('.modal, .o_dialog')
                            ?.querySelector('[special="cancel"], .o_form_button_cancel, button[data-dismiss]');
                        if (btnCancel) btnCancel.click();

                        await env.services.action.doAction({
                            type:      'ir.actions.act_window',
                            name:      'Confirmar verificación de huella',
                            res_model: 'zk.biometric.confirm.wizard',
                            views:     [[false, 'form']],  
                            view_mode: 'form',
                            target:    'new',
                            size:      'small',
                            context:   action.params?.confirm_context || {},
                        });
                    }, 1500);
                }

            } catch (err) {
                const msg = err?.data?.message || err?.message || '';
                _handleZkError(msg, env.services.notification);
            }

            running = false;
        }, 3000);
    });
}

actionRegistry.add('zk_start_verify_polling', zkStartVerifyPolling);