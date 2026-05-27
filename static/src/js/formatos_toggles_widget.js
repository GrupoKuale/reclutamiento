/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, onWillStart, onWillUpdateProps, xml } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class FormatosTogglesWidget extends Component {
    static template = xml`
        <div class="o_formatos_toggles">
            <t t-if="state.loading">
                <span class="text-muted">Cargando formatos...</span>
            </t>
            <t t-else="">
                <t t-if="state.formatos.length === 0">
                    <span class="text-muted" style="font-style:italic;">
                        No hay formatos disponibles.
                    </span>
                </t>
                <t t-foreach="state.formatos" t-as="formato" t-key="formato.id">
                    <div style="display:flex; align-items:center; margin-bottom:8px; gap:10px;">
                        <span style="font-size:0.95em; min-width:220px; user-select:none;">
                            <t t-esc="formato.name"/>
                        </span>
                        <div class="o_field_boolean_toggle">
                            <div class="form-check form-switch">
                                <input
                                    type="checkbox"
                                    class="form-check-input"
                                    role="switch"
                                    t-att-id="'formato_toggle_' + formato.id"
                                    t-att-checked="formato.enabled"
                                    t-att-disabled="props.readonly or false"
                                    t-on-change="(ev) => this.onToggleChange(formato.id, ev.target.checked)"
                                />
                                <label
                                    class="form-check-label"
                                    t-att-for="'formato_toggle_' + formato.id">
                                </label>
                            </div>
                        </div>
                    </div>
                </t>
            </t>
        </div>
    `;

    static props = {
        record: { type: Object },
        readonly: { type: Boolean, optional: true },
        name: { type: String, optional: true },
        id: { optional: true },
    };

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            formatos: [],
            loading: true,
        });

        onWillStart(async () => {
            await this._loadFormatos();
        });

        onWillUpdateProps(async (nextProps) => {
            await this._loadFormatos(nextProps);
        });
    }

    async _getSelectedIdsFromServer(props) {
        const p = props || this.props;
        const jobId = p.record.resId || p.record.data?.id;
        if (!jobId) return [];
        try {
            const result = await this.orm.read('hr.job', [jobId], ['formatos_ids']);
            if (result && result[0] && result[0].formatos_ids) {
                return result[0].formatos_ids;
            }
        } catch (e) {
            console.log("Error leyendo formatos:", e);
        }
        return [];
    }

    async _loadFormatos(props) {
        const allFormatos = await this.orm.searchRead(
            "reclutamiento__kuale.format_employee",
            [["active", "=", true]],
            ["id", "name"],
            { order: "name asc" }
        );
        const selectedIds = await this._getSelectedIdsFromServer(props);
        this.state.formatos = allFormatos.map((f) => ({
            id: f.id,
            name: f.name,
            enabled: selectedIds.includes(f.id),
        }));
        this.state.loading = false;
    }

    async onToggleChange(formatoId, newValue) {
        if (this.props.readonly) return;

        const newFormatos = this.state.formatos.map((f) =>
            f.id === formatoId ? { ...f, enabled: newValue } : { ...f }
        );

        const enabledIds = newFormatos.filter((f) => f.enabled).map((f) => f.id);
        this.state.formatos = newFormatos;

        const jobId = this.props.record.resId || this.props.record.data?.id;
        if (jobId) {
            await this.orm.write('hr.job', [jobId], {
                formatos_ids: [[6, 0, enabledIds]],
            });
        }
    }
}

registry.category("fields").add("formatos_toggles", {
    component: FormatosTogglesWidget,
    supportedTypes: ["many2many"],
    extractProps({ attrs, field }, dynamicInfo) {
        return {
            readonly: dynamicInfo.readonly,
        };
    },
});