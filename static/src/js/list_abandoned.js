/** @odoo-module **/
import { ListRenderer } from "@web/views/list/list_renderer";
import { ListController } from "@web/views/list/list_controller";
import { patch } from "@web/core/utils/patch";

patch(ListRenderer.prototype, {
    getRowClass(record) {
        const cls = super.getRowClass(record);
        if (record.data.abandoned) {
            return cls + " o_list_row_abandoned";
        }
        return cls;
    },
    onClickRow(record, ev) {
        if (record.data.abandoned) {
            ev.stopPropagation();
            ev.preventDefault();
            return;
        }
        return super.onClickRow(record, ev);
    },
});

patch(ListController.prototype, {
    getStaticActionMenuItems() {
        const items = super.getStaticActionMenuItems(...arguments);
        const selectedRecords = this.model.root.selection;
        if (!selectedRecords?.length) return items;

        const hasArchived  = selectedRecords.some(r => r.data.active === false);
        const hasActive    = selectedRecords.some(r => r.data.active !== false);
        const allAbandoned = selectedRecords.every(r => r.data.abandoned === true);

        const result = { ...items };

        if (hasActive && !hasArchived) {
            delete result.unarchive;
        } else if (hasArchived && !hasActive) {
            delete result.archive;
        }

        if (allAbandoned) {
            delete result.export;
            delete result.duplicate;
        }

        return result;
    },

    get actionMenuItems() {
        const items = super.actionMenuItems;
        const selectedRecords = this.model.root.selection;
        if (!selectedRecords?.length) return items;

        const allAbandoned = selectedRecords.every(r => r.data.abandoned === true);
        if (!allAbandoned) return items;

        const hiddenIds = [597, 586, 587]; // Send SMS, Enviar correo, Rechazar

        return {
            ...items,
            action: (items.action || []).filter(item => {
                if (item.id && hiddenIds.includes(item.id)) return false;
                return true;
            }),
        };
    },
});