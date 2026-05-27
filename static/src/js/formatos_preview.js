/** @odoo-module **/

import { FormController } from "@web/views/form/form_controller";
import { registry } from "@web/core/registry";
import { formView } from "@web/views/form/form_view";
import { onMounted, onPatched } from "@odoo/owl";

class FormatosPreviewFormController extends FormController {
    setup() {
        super.setup();
        onMounted(() => this._applyBackground());
        onPatched(() => this._applyBackground());
    }

    _applyBackground() {
        // Leer el valor de hoja_url del modelo
        const record = this.model.root;
        if (!record) return;
        const hojaUrl = record.data.hoja_url || '';
        const bg = document.getElementById('kuale_membretada_bg');
        if (bg && hojaUrl) {
            bg.style.backgroundImage = `url("${hojaUrl}")`;
        }
    }
}

registry.category("views").add("formatos_preview_form", {
    ...formView,
    Controller: FormatosPreviewFormController,
});