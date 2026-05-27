/** @odoo-module **/
import { Component, useState, onWillStart } from "@odoo/owl";
import { registry }               from "@web/core/registry";
import { useService }             from "@web/core/utils/hooks";
import { _t }                     from "@web/core/l10n/translation";
import { standardFieldProps }     from "@web/views/fields/standard_field_props";

const DOC_LABELS = {
    imss_aviso:            'Aviso de afiliación al IMSS',
    curp:                  'CURP',
    rfc_constancia:        'Constancia de RFC',
    santander:             'Contrato apertura cuenta Nómina Santander',
    ine:                   'INE',
    acta_nacimiento:       'Acta de nacimiento',
    comprobante_estudios:  'Último comprobante de estudios',
    carta_recomendacion:   'Cartas de recomendación',
    comprobante_domicilio: 'Comprobante de domicilio',
};

const DOC_ORDER = Object.keys(DOC_LABELS);

class DocumentationPanelWidget extends Component {
    static template = "reclutamiento__kuale.DocumentationPanelWidget";
    static props    = { ...standardFieldProps };

    setup() {
        this.orm          = useService("orm");
        this.notification = useService("notification");
        this.state        = useState({
            docs:       [],
            loading:    true,
            scanningId: null,
            scannerOk:  null,
            scannerMsg: '',
            scannerDev: '',
        });
        onWillStart(async () => {
            await this._loadDocs();
            await this._checkScanner();
        });
    }

    get applicantId() {
        try {
            const root = this.props.record.model.root;
            const id   = root?.data?.id || root?.resId;
            console.log("applicantId desde root:", id);
            return id || null;
        } catch (e) {
            console.error("Error obteniendo applicantId:", e);
            return null;
        }
    }

    async _loadDocs() {
        if (!this.applicantId) { this.state.loading = false; return; }
        try {
            const rows = await this.orm.searchRead(
                'hr.applicant.documentation',
                [['applicant_id', '=', this.applicantId]],
                ['id', 'doc_type', 'doc_name', 'state', 'attachment_id', 'migrated'],
                { order: 'id asc' }
            );
            const byType = Object.fromEntries(rows.map(r => [r.doc_type, r]));
            this.state.docs = DOC_ORDER
                .filter(k => byType[k])
                .map(k => ({ ...byType[k], label: DOC_LABELS[k] }));
        } catch (e) {
            console.error('Error cargando docs:', e);
        } finally {
            this.state.loading = false;
        }
    }

    async _checkScanner() {
        try {
            const res    = await fetch('/kuale/scan/status', {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body:    JSON.stringify({ jsonrpc: '2.0', method: 'call', id: 1, params: {} }),
            });
            const json   = await res.json();
            const result = json.result ?? {};
            this.state.scannerOk  = result.available  ?? false;
            this.state.scannerDev = result.device      ?? '';
            this.state.scannerMsg = result.diagnostics ?? result.error ?? '';
        } catch {
            this.state.scannerOk  = false;
            this.state.scannerMsg = 'No se pudo conectar con el servidor.';
        }
    }

    // ── Escaneo principal — inicia el flujo multipágina ───────────────────
    async onScan(doc) {
        if (this.state.scanningId !== null) return;
        await this._scanFlow(doc);
    }

    async _scanFlow(doc) {
        this.state.scanningId = doc.id;
        let pageCount = 0;

        try {
            // 1. Escanear primera página
            const firstResult = await this._scanPage(doc.id);
            if (!firstResult?.success) {
                this.notification.add(
                    _t('Error: ') + (firstResult?.error || _t('Error desconocido')),
                    { type: 'danger', sticky: true }
                );
                return;
            }
            pageCount = firstResult.page_count;

            // 2. Preguntar si hay más hojas y seguir escaneando
            while (true) {
                const hasMore = await this._askMorePages(pageCount);
                if (!hasMore) break;

                this.state.scanningId = doc.id;
                const nextResult = await this._scanPage(doc.id);
                if (!nextResult?.success) {
                    this.notification.add(
                        _t('Error escaneando página: ') + (nextResult?.error || ''),
                        { type: 'danger', sticky: true }
                    );
                    break;
                }
                pageCount = nextResult.page_count;
            }

            // 3. Unir todas las páginas y guardar
            this.state.scanningId = doc.id;
            const mergeResult = await this._mergeAndSave(doc.id);

            if (mergeResult?.success) {
                const hojas = pageCount === 1 ? '1 hoja' : `${pageCount} hojas`;
                this.notification.add(
                    _t(`Documento guardado (${hojas})`),
                    { type: 'success' }
                );
                this._patch(doc.id, {
                    state:         'scanned',
                    doc_name:      mergeResult.filename,
                    attachment_id: [mergeResult.attachment_id, mergeResult.filename],
                    _previewUrl:   mergeResult.preview_url,
                });
                this.state.scannerOk  = true;
                this.state.scannerMsg = '';

                // Recargar el registro para que aparezcan los archivos en el chatter
                try {
                    await this.props.record.model.root.load();
                    this.props.record.model.notify();
                } catch (e) {
                    console.warn('No se pudo recargar el registro:', e);
                }
            } else {
                this.notification.add(
                    _t('Error guardando: ') + (mergeResult?.error || ''),
                    { type: 'danger', sticky: true }
                );
            }

        } catch (e) {
            console.error('Error en _scanFlow:', e);
            this.notification.add(_t('Error en el proceso de escaneo.'), { type: 'danger' });
        } finally {
            this.state.scanningId = null;
        }
    }

    // Escanea una página y la guarda en sesión del servidor
    async _scanPage(docId) {
        try {
            const res  = await fetch(`/kuale/scan/page/${docId}`, {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body:    JSON.stringify({ jsonrpc: '2.0', method: 'call', id: 1, params: {} }),
            });
            const json = await res.json();
            return json.result;
        } catch (e) {
            console.error('Error _scanPage:', e);
            return { success: false, error: String(e) };
        }
    }

    // Une todas las páginas en sesión y guarda el PDF final
    async _mergeAndSave(docId) {
        try {
            const res  = await fetch(`/kuale/scan/merge/${docId}`, {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body:    JSON.stringify({ jsonrpc: '2.0', method: 'call', id: 1, params: {} }),
            });
            const json = await res.json();
            return json.result;
        } catch (e) {
            console.error('Error _mergeAndSave:', e);
            return { success: false, error: String(e) };
        }
    }

    // Modal: ¿hay más hojas?
    _askMorePages(pageCount) {
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
                        <button id="kuale_no_more"
                            style="flex:1; background:#27ae60; color:#fff; border:none; border-radius:999px;
                                   padding:12px 20px; font-size:14px; font-weight:700; cursor:pointer;">
                            No, listo ✓
                        </button>
                        <button id="kuale_yes_more"
                            style="flex:1; background:#3498db; color:#fff; border:none; border-radius:999px;
                                   padding:12px 20px; font-size:14px; font-weight:700; cursor:pointer;">
                            Sí, otra hoja
                        </button>
                    </div>
                </div>
            `;
            document.body.appendChild(overlay);
            overlay.querySelector('#kuale_yes_more').addEventListener('click', () => {
                document.body.removeChild(overlay);
                resolve(true);
            });
            overlay.querySelector('#kuale_no_more').addEventListener('click', () => {
                document.body.removeChild(overlay);
                resolve(false);
            });
        });
    }

    // ── Ver documento ─────────────────────────────────────────────────────
    onPreview(doc) {
        const id = Array.isArray(doc.attachment_id) ? doc.attachment_id[0] : doc.attachment_id;
        if (!id) return;
        window.open(doc._previewUrl || `/web/content/${id}?download=false`, '_blank');
    }

    // ── Quitar documento ──────────────────────────────────────────────────
    async onRemove(doc) {
        const confirmed = await this._showConfirmModal(doc.label);
        if (!confirmed) return;
        try {
            await this.orm.call('hr.applicant.documentation', 'action_remove', [[doc.id]]);
            this.notification.add(_t('Documento eliminado.'), { type: 'info' });
            this._patch(doc.id, {
                state:         'pending',
                doc_name:      false,
                attachment_id: false,
                _previewUrl:   null,
            });

            // Recargar el registro para que desaparezca del chatter
            try {
                await this.props.record.model.root.load();
                this.props.record.model.notify();
            } catch (e) {
                console.warn('No se pudo recargar el registro:', e);
            }
        } catch {
            this.notification.add(_t('Error al eliminar.'), { type: 'danger' });
        }
    }

    // Modal confirmación de eliminación
    _showConfirmModal(docLabel) {
        return new Promise((resolve) => {
            const overlay = document.createElement('div');
            overlay.style.cssText = `
                position:fixed; inset:0; z-index:99999;
                background:rgba(0,0,0,.6); backdrop-filter:blur(4px);
                display:flex; align-items:center; justify-content:center;
            `;
            overlay.innerHTML = `
                <div style="background:#fff; border-radius:12px; padding:32px 28px;
                            max-width:420px; width:90%; box-shadow:0 24px 64px rgba(0,0,0,.3);
                            font-family:inherit; text-align:center;">
                    <div style="font-size:40px; margin-bottom:12px;">⚠️</div>
                    <h4 style="font-size:17px; font-weight:700; color:#111; margin-bottom:10px;">
                        ¿Eliminar documento?
                    </h4>
                    <p style="font-size:13px; color:#555; line-height:1.6; margin-bottom:24px;">
                        Estás a punto de eliminar <strong>${docLabel}</strong>.<br/>
                        El archivo se quitará de la sección de documentación y de los archivos adjuntos.<br/>
                        <span style="color:#e74c3c; font-weight:600;">Esta acción no se puede deshacer.</span>
                    </p>
                    <div style="display:flex; gap:12px; justify-content:center;">
                        <button id="kuale_cancel_remove"
                            style="flex:1; background:#f5f5f5; color:#333; border:none; border-radius:999px;
                                   padding:12px 20px; font-size:14px; font-weight:700; cursor:pointer;">
                            Cancelar
                        </button>
                        <button id="kuale_confirm_remove"
                            style="flex:1; background:#e74c3c; color:#fff; border:none; border-radius:999px;
                                   padding:12px 20px; font-size:14px; font-weight:700; cursor:pointer;">
                            Sí, eliminar
                        </button>
                    </div>
                </div>
            `;
            document.body.appendChild(overlay);
            overlay.querySelector('#kuale_confirm_remove').addEventListener('click', () => {
                document.body.removeChild(overlay);
                resolve(true);
            });
            overlay.querySelector('#kuale_cancel_remove').addEventListener('click', () => {
                document.body.removeChild(overlay);
                resolve(false);
            });
        });
    }

    // ── Confirmar documento ───────────────────────────────────────────────
    async onConfirm(doc) {
        try {
            await this.orm.call('hr.applicant.documentation', 'action_confirm', [[doc.id]]);
            this.notification.add(_t('Documento confirmado ✓'), { type: 'success' });
            this._patch(doc.id, { state: 'confirmed' });
        } catch {
            this.notification.add(_t('Error al confirmar.'), { type: 'danger' });
        }
    }

    // ── Helpers ───────────────────────────────────────────────────────────
    _patch(id, changes) {
        const i = this.state.docs.findIndex(d => d.id === id);
        if (i !== -1) this.state.docs[i] = { ...this.state.docs[i], ...changes };
    }

    get confirmedCount()  { return this.state.docs.filter(d => d.state === 'confirmed').length; }
    get totalCount()      { return this.state.docs.length; }
    get progressPercent() { return this.totalCount ? Math.round(this.confirmedCount / this.totalCount * 100) : 0; }

    stateLabel(s) { return { pending: 'Pendiente', scanned: 'Escaneado', confirmed: 'Confirmado' }[s] || s; }
    stateColor(s) { return s === 'confirmed' ? '#27ae60' : s === 'scanned' ? '#f39c12' : '#bdc3c7'; }
    stateIcon(s)  { return s === 'confirmed' ? '✓' : s === 'scanned' ? '↑' : '○'; }

    // ── Escaneo múltiple global ───────────────────────────────────────────────
    async onScanAll() {
        if (this.state.scanningId !== null) return;

        // Filtrar solo los pendientes (sin documento)
        const pending = this.state.docs.filter(d => d.state === 'pending');

        if (pending.length === 0) {
            this.notification.add(_t('No hay documentos pendientes.'), { type: 'info' });
            return;
        }

        const confirmed = await this._showScanAllConfirm(pending);
        if (!confirmed) return;

        let scanned = 0;
        let skipped = 0;
        let errors  = 0;

        for (let i = 0; i < pending.length; i++) {
            const doc = pending[i];

            // Mostrar modal de progreso (no bloqueante)
            this._updateProgressModal(i, pending.length, doc.label);

            const proceed = await this._askScanThisDoc(doc.label, i + 1, pending.length);
            if (!proceed) {
                skipped++;
                continue;
            }

            try {
                await this._scanFlow(doc);
                scanned++;
            } catch (e) {
                console.error('Error escaneando', doc.label, e);
                errors++;
            }
        }

        this._closeProgressModal();
        this.notification.add(
            _t(`Escaneo completo: ${scanned} guardados, ${skipped} omitidos${errors ? ', ' + errors + ' errores' : ''}.`),
            { type: scanned > 0 ? 'success' : 'warning', sticky: true }
        );
    }

    _showScanAllConfirm(pending) {
        return new Promise((resolve) => {
            const overlay = document.createElement('div');
            overlay.id = 'kuale_scanall_confirm';
            overlay.style.cssText = `
                position:fixed; inset:0; z-index:99999;
                background:rgba(0,0,0,.6); backdrop-filter:blur(4px);
                display:flex; align-items:center; justify-content:center;
            `;
            const list = pending.map((d, i) =>
                `<li style="padding:4px 0; color:#555; font-size:13px;">
                    <span style="color:#3498db; font-weight:700;">${i + 1}.</span> ${d.label}
                </li>`
            ).join('');
            overlay.innerHTML = `
                <div style="background:#fff; border-radius:12px; padding:32px 28px;
                            max-width:460px; width:90%; box-shadow:0 24px 64px rgba(0,0,0,.3);
                            font-family:inherit;">
                    <div style="text-align:center; font-size:40px; margin-bottom:12px;">🗂️</div>
                    <h4 style="font-size:17px; font-weight:700; color:#111; margin-bottom:8px; text-align:center;">
                        Escaneo múltiple
                    </h4>
                    <p style="font-size:13px; color:#555; margin-bottom:12px; text-align:center;">
                        Se escanearán <strong>${pending.length}</strong> documentos pendientes en este orden:
                    </p>
                    <ul style="list-style:none; padding:0 8px; margin-bottom:24px; max-height:200px; overflow-y:auto;">
                        ${list}
                    </ul>
                    <div style="display:flex; gap:12px; justify-content:center;">
                        <button id="kuale_scanall_cancel"
                            style="flex:1; background:#f5f5f5; color:#333; border:none; border-radius:999px;
                                padding:12px 20px; font-size:14px; font-weight:700; cursor:pointer;">
                            Cancelar
                        </button>
                        <button id="kuale_scanall_start"
                            style="flex:1; background:#2980b9; color:#fff; border:none; border-radius:999px;
                                padding:12px 20px; font-size:14px; font-weight:700; cursor:pointer;">
                            Iniciar escaneo
                        </button>
                    </div>
                </div>
            `;
            document.body.appendChild(overlay);
            overlay.querySelector('#kuale_scanall_start').addEventListener('click', () => {
                document.body.removeChild(overlay);
                resolve(true);
            });
            overlay.querySelector('#kuale_scanall_cancel').addEventListener('click', () => {
                document.body.removeChild(overlay);
                resolve(false);
            });
        });
    }

    _askScanThisDoc(label, current, total) {
        return new Promise((resolve) => {
            const overlay = document.createElement('div');
            overlay.id = 'kuale_scanall_next';
            overlay.style.cssText = `
                position:fixed; inset:0; z-index:99999;
                background:rgba(0,0,0,.6); backdrop-filter:blur(4px);
                display:flex; align-items:center; justify-content:center;
            `;
            overlay.innerHTML = `
                <div style="background:#fff; border-radius:12px; padding:32px 28px;
                            max-width:420px; width:90%; box-shadow:0 24px 64px rgba(0,0,0,.3);
                            font-family:inherit; text-align:center;">
                    <div style="font-size:13px; color:#999; margin-bottom:8px;">
                        Documento ${current} de ${total}
                    </div>
                    <div style="font-size:36px; margin-bottom:12px;">📄</div>
                    <h4 style="font-size:17px; font-weight:700; color:#111; margin-bottom:10px;">
                        ${label}
                    </h4>
                    <p style="font-size:13px; color:#555; line-height:1.6; margin-bottom:24px;">
                        Coloca el documento en el escáner y presiona <strong>Escanear</strong>.<br/>
                        O presiona <strong>Omitir</strong> para saltarlo.
                    </p>
                    <div style="display:flex; gap:12px; justify-content:center;">
                        <button id="kuale_skip_doc"
                            style="flex:1; background:#f5f5f5; color:#333; border:none; border-radius:999px;
                                padding:12px 20px; font-size:14px; font-weight:700; cursor:pointer;">
                            Omitir
                        </button>
                        <button id="kuale_scan_doc"
                            style="flex:1; background:#27ae60; color:#fff; border:none; border-radius:999px;
                                padding:12px 20px; font-size:14px; font-weight:700; cursor:pointer;">
                            Escanear ↑
                        </button>
                    </div>
                </div>
            `;
            document.body.appendChild(overlay);
            overlay.querySelector('#kuale_scan_doc').addEventListener('click', () => {
                document.body.removeChild(overlay);
                resolve(true);
            });
            overlay.querySelector('#kuale_skip_doc').addEventListener('click', () => {
                document.body.removeChild(overlay);
                resolve(false);
            });
        });
    }

    _updateProgressModal(current, total, label) {
        let overlay = document.getElementById('kuale_progress_modal');
        const pct   = Math.round((current / total) * 100);
        const html  = `
            <div style="background:#fff; border-radius:12px; padding:28px;
                        max-width:400px; width:90%; box-shadow:0 24px 64px rgba(0,0,0,.3);
                        font-family:inherit; text-align:center;">
                <div style="font-size:13px; color:#999; margin-bottom:6px;">
                    Progreso general
                </div>
                <div style="font-size:15px; font-weight:700; color:#111; margin-bottom:16px;">
                    ${current} de ${total} — ${label}
                </div>
                <div style="background:#eee; border-radius:999px; height:10px; overflow:hidden;">
                    <div style="background:#2980b9; width:${pct}%; height:100%;
                                transition:width .4s ease; border-radius:999px;"></div>
                </div>
                <div style="margin-top:10px; font-size:12px; color:#aaa;">${pct}%</div>
            </div>
        `;
        if (!overlay) {
            overlay    = document.createElement('div');
            overlay.id = 'kuale_progress_modal';
            overlay.style.cssText = `
                position:fixed; bottom:24px; right:24px; z-index:99998;
                display:flex; align-items:center; justify-content:center;
            `;
            document.body.appendChild(overlay);
        }
        overlay.innerHTML = html;
    }

    _closeProgressModal() {
        const el = document.getElementById('kuale_progress_modal');
        if (el) document.body.removeChild(el);
    }
}

registry.category('fields').add('documentation_panel_widget', {
    component:      DocumentationPanelWidget,
    supportedTypes: ['one2many'],
});