/** @odoo-module **/

import { registry } from "@web/core/registry";

const actionRegistry = registry.category("actions");

// ── Helpers compartidos ──────────────────────────────────────────────────────

async function _scanPage(url) {
    const res  = await fetch(url, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ jsonrpc: '2.0', method: 'call', id: 1, params: {} }),
    });
    const json = await res.json();
    return json.result;
}

async function _mergePage(url) {
    const res  = await fetch(url, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ jsonrpc: '2.0', method: 'call', id: 1, params: {} }),
    });
    const json = await res.json();
    return json.result;
}

function _askMorePages(pageCount) {
    return new Promise((resolve) => {
        const overlay = document.createElement('div');
        overlay.style.cssText = `
            position:fixed; inset:0; z-index:99999;
            background:rgba(0,0,0,.6); backdrop-filter:blur(4px);
            display:flex; align-items:center; justify-content:center;
        `;
        overlay.innerHTML = `
            <div style="background:#fff; border-radius:12px; padding:32px 28px;
                        max-width:400px; width:90%; box-shadow:0 24px 64px rgba(0,0,0,.3);
                        font-family:inherit; text-align:center;">
                <div style="font-size:40px; margin-bottom:12px;">📄</div>
                <h4 style="font-size:17px; font-weight:700; color:#111; margin-bottom:10px;">
                    Página ${pageCount} escaneada
                </h4>
                <p style="font-size:13px; color:#555; line-height:1.6; margin-bottom:24px;">
                    ¿El documento tiene más hojas?
                </p>
                <div style="display:flex; gap:12px; justify-content:center;">
                    <button id="fmt_no_more"
                        style="flex:1; background:#27ae60; color:#fff; border:none; border-radius:999px;
                               padding:12px 20px; font-size:14px; font-weight:700; cursor:pointer;">
                        No, listo ✓
                    </button>
                    <button id="fmt_yes_more"
                        style="flex:1; background:#3498db; color:#fff; border:none; border-radius:999px;
                               padding:12px 20px; font-size:14px; font-weight:700; cursor:pointer;">
                        Sí, otra hoja
                    </button>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);
        overlay.querySelector('#fmt_yes_more').addEventListener('click', () => {
            document.body.removeChild(overlay);
            resolve(true);
        });
        overlay.querySelector('#fmt_no_more').addEventListener('click', () => {
            document.body.removeChild(overlay);
            resolve(false);
        });
    });
}

function _showProgress(label) {
    let el = document.getElementById('kuale_fmt_scan_progress');
    if (!el) {
        el    = document.createElement('div');
        el.id = 'kuale_fmt_scan_progress';
        el.style.cssText = `
            position:fixed; inset:0; z-index:99998;
            background:rgba(0,0,0,.5); backdrop-filter:blur(3px);
            display:flex; align-items:center; justify-content:center;
        `;
        document.body.appendChild(el);
    }
    el.innerHTML = `
        <div style="background:#fff; border-radius:12px; padding:28px 24px;
                    max-width:360px; width:90%; text-align:center; font-family:inherit;">
            <div style="font-size:32px; margin-bottom:12px;">🖨️</div>
            <p style="font-size:15px; font-weight:600; color:#111; margin:0 0 6px;">
                Escaneando…
            </p>
            <p style="font-size:13px; color:#555; margin:0;">${label}</p>
            <div style="margin-top:16px; height:4px; background:#e0e7ff; border-radius:4px; overflow:hidden;">
                <div style="height:100%; width:40%; background:#6366f1; border-radius:4px;
                            animation: kuale_scan_slide 1.2s ease-in-out infinite;"></div>
            </div>
        </div>
        <style>
            @keyframes kuale_scan_slide {
                0%   { margin-left:0;   width:30%; }
                50%  { margin-left:50%; width:40%; }
                100% { margin-left:0;   width:30%; }
            }
        </style>
    `;
}

function _hideProgress() {
    const el = document.getElementById('kuale_fmt_scan_progress');
    if (el) document.body.removeChild(el);
}

function _reloadWizard(env, wizardId) {
    try {
        env.services.action.doAction(
            {
                type:      'ir.actions.act_window',
                res_model: 'reclutamiento__kuale.formatos_wizard',
                res_id:    wizardId,
                views:     [[false, 'form']],
                target:    'new',
                context:   { dialog_size: 'medium' },
            },
            { clearBreadcrumbs: false }
        );
    } catch (e) {
        console.warn('No se pudo recargar el wizard:', e);
        env.services.notification.add(
            'Escaneo exitoso. Cierra y vuelve a abrir el wizard para ver el archivo.',
            { type: 'info' }
        );
    }
}

// ── Flujo genérico de escaneo multipágina ────────────────────────────────────
async function _scanFlow(env, pageUrl, mergeUrl, label, wizardId) {
    let pageCount = 0;
    try {
        _showProgress(label);
        const firstResult = await _scanPage(pageUrl);
        _hideProgress();
        if (!firstResult?.success) {
            env.services.notification.add(
                'Error al escanear: ' + (firstResult?.error || 'Error desconocido'),
                { type: 'danger', sticky: true }
            );
            return;
        }
        pageCount = firstResult.page_count;
        while (true) {
            const hasMore = await _askMorePages(pageCount);
            if (!hasMore) break;
            _showProgress(label);
            const nextResult = await _scanPage(pageUrl);
            _hideProgress();
            if (!nextResult?.success) {
                env.services.notification.add(
                    'Error en página ' + (pageCount + 1) + ': ' + (nextResult?.error || ''),
                    { type: 'danger', sticky: true }
                );
                break;
            }
            pageCount = nextResult.page_count;
        }
        _showProgress('Guardando documento…');
        const mergeResult = await _mergePage(mergeUrl);
        _hideProgress();
        if (mergeResult?.success) {
            const hojas = pageCount === 1 ? '1 hoja' : `${pageCount} hojas`;
            env.services.notification.add(
                `Escaneado correctamente (${hojas}). Confirma para finalizar.`,
                { type: 'success' }
            );
            _reloadWizard(env, wizardId);
        } else {
            env.services.notification.add(
                'Error guardando: ' + (mergeResult?.error || ''),
                { type: 'danger', sticky: true }
            );
        }
    } catch (e) {
        _hideProgress();
        console.error('Error en _scanFlow:', e);
        env.services.notification.add('Error inesperado en el escaneo.', { type: 'danger' });
    }
}

// ── Actions de escaneo ───────────────────────────────────────────────────────
async function kualeEscanearFormato(env, action) {
    const lineId   = action.params?.line_id;
    const wizardId = action.params?.wizard_id;
    const label    = action.params?.doc_label || 'Formato';
    if (!lineId) {
        env.services.notification.add('Error: no se recibió el ID de la línea.', { type: 'danger' });
        return;
    }
    await _scanFlow(env, `/kuale/scan/formato/page/${lineId}`, `/kuale/scan/formato/merge/${lineId}`, label, wizardId);
}
actionRegistry.add('kuale_scan_formato', kualeEscanearFormato);

async function kualeEscanearContrato(env, action) {
    const wizardId = action.params?.wizard_id;
    const label    = action.params?.doc_label || 'Contrato firmado';
    if (!wizardId) {
        env.services.notification.add('Error: no se recibió el ID del wizard.', { type: 'danger' });
        return;
    }
    await _scanFlow(env, `/kuale/scan/contrato/page/${wizardId}`, `/kuale/scan/contrato/merge/${wizardId}`, label, wizardId);
}
actionRegistry.add('kuale_scan_contrato', kualeEscanearContrato);

async function kualeEscanearFormatoContratacion(env, action) {
    const wizardId = action.params?.wizard_id;
    const label    = action.params?.doc_label || 'Formato de Contratación GK';
    if (!wizardId) {
        env.services.notification.add('Error: no se recibió el ID del wizard.', { type: 'danger' });
        return;
    }
    await _scanFlow(env, `/kuale/scan/formato_contratacion/page/${wizardId}`, `/kuale/scan/formato_contratacion/merge/${wizardId}`, label, wizardId);
}
actionRegistry.add('kuale_scan_formato_contratacion', kualeEscanearFormatoContratacion);

// ── Action: kuale_download_and_action ────────────────────────────────────────
async function kualeDownloadAndAction(env, action) {
    const downloadUrl = action.params?.download_url;
    let nextAction    = action.params?.next_action;

    // next_action puede llegar como string JSON serializado — parsear si es necesario
    if (typeof nextAction === 'string') {
        try {
            nextAction = JSON.parse(nextAction);
        } catch(e) {
            console.warn('No se pudo parsear next_action:', e);
            nextAction = null;
        }
    }

    // 1. Descargar en nueva pestaña
    if (downloadUrl) {
        window.open(downloadUrl, '_blank');
    }

    // 2. Cerrar este dialog con act_window_close — esto cierra el dialog
    //    actual (el más reciente en el stack) sin cerrar los anteriores
    await env.services.action.doAction(
        { type: 'ir.actions.act_window_close' },
        { clearBreadcrumbs: false }
    );

    // 3. Esperar a que Odoo procese el cierre
    await new Promise(resolve => setTimeout(resolve, 300));

    // 4. Abrir el wizard principal
    if (nextAction) {
        try {
            await env.services.action.doAction(nextAction, { clearBreadcrumbs: false });
        } catch (e) {
            console.warn('kuale_download_and_action: error en next_action', e);
        }
    }
}
actionRegistry.add('kuale_download_and_action', kualeDownloadAndAction);

// ── Action: kuale_generar_formato_contratacion ────────────────────────────────
// Recibe download_url y formatos_wizard_id directamente (sin next_action complejo).
// 1. Abre la descarga con window.open
// 2. Abre el wizard principal con doAction — como NO hay next_action que parsear,
//    no hay error de .map()
async function kualeGenerarFormatoContratacion(env, action) {
    const downloadUrl      = action.params?.download_url;
    const formatosWizardId = action.params?.formatos_wizard_id;

    // 1. Descargar — window.open no toca el stack de Odoo
    if (downloadUrl) {
        window.open(downloadUrl, '_blank');
    }

    // 2. Abrir wizard principal — doAction con target:'new' sobre un wizard
    //    existente REEMPLAZA el dialog actual en Odoo 17
    if (formatosWizardId) {
        try {
            await env.services.action.doAction({
                type:      'ir.actions.act_window',
                res_model: 'reclutamiento__kuale.formatos_wizard',
                view_mode: 'form',
                res_id:    formatosWizardId,
                views:     [[false, 'form']],
                target:    'new',
                context:   { dialog_size: 'medium' },
            }, { clearBreadcrumbs: false });
        } catch (e) {
            console.warn('kualeGenerarFormatoContratacion: error abriendo wizard', e);
        }
    } else {
        // Sin wizard principal, solo cerrar
        try {
            await env.services.action.doAction(
                { type: 'ir.actions.act_window_close' },
                { clearBreadcrumbs: false }
            );
        } catch (e) {}
    }
}
actionRegistry.add('kuale_generar_formato_contratacion', kualeGenerarFormatoContratacion);

// ── Action: kuale_generar_contrato ────────────────────────────────────────────
async function kualeGenerarContrato(env, action) {
    const downloadUrl      = action.params?.download_url;
    const formatosWizardId = action.params?.formatos_wizard_id;

    if (downloadUrl) {
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.setAttribute('download', '');
        link.style.display = 'none';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    if (formatosWizardId) {
        try {
            await env.services.action.doAction({
                type:      'ir.actions.act_window',
                res_model: 'reclutamiento__kuale.formatos_wizard',
                view_mode: 'form',
                res_id:    formatosWizardId,
                views:     [[false, 'form']],
                target:    'new',
                context:   { dialog_size: 'medium' },
            }, { clearBreadcrumbs: false });
        } catch (e) {
            console.warn('kualeGenerarContrato: error abriendo wizard', e);
        }
    } else {
        try {
            await env.services.action.doAction(
                { type: 'ir.actions.act_window_close' },
                { clearBreadcrumbs: false }
            );
        } catch (e) {}
    }
}
actionRegistry.add('kuale_generar_contrato', kualeGenerarContrato);