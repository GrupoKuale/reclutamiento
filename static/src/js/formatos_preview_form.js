/** @odoo-module **/

import { registry } from "@web/core/registry";
import { FormController } from "@web/views/form/form_controller";
import { formView } from "@web/views/form/form_view";
import { onMounted, onPatched } from "@odoo/owl";

class KualeFormatosPreviewController extends FormController {

    setup() {
        super.setup();

        onMounted(() => {
            setTimeout(() => this._applyBg(), 300);
        });

        onPatched(() => {
            setTimeout(() => this._applyBg(), 100);
        });
    }

    async onWillStart() {
        await super.onWillStart();
    }

    _applyBg() {
        const record = this.model.root;
        const hojaUrl = record.data.hoja_url || '';
        const absUrl = hojaUrl.startsWith('http')
            ? hojaUrl
            : window.location.origin + hojaUrl;

        const bg = document.getElementById('kuale_membretada_bg');
        if (bg && absUrl) {
            bg.style.backgroundImage = `url('${absUrl}')`;
        }
    }
}

registry.category("views").add("kuale_formatos_preview", {
    ...formView,
    Controller: KualeFormatosPreviewController,
});