/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { PriorityField } from "@web/views/fields/priority/priority_field";
import { xml } from "@odoo/owl";

const COMPANY_ICONS = {
    "Carl's Jr."        : "🍔",
    "Dairy Queen"       : "🍦",
    "Hidrológica"       : "💧",
    "Publipuentes"      : "📢",
    "Mister Motor"      : "⚙️",
    "Tintocinco"        : "👕",
    "Inmobiliaria Erben": "🏠",
};

const COMPANY_ALIASES = {
    "Carl's"                              : "Carl's Jr.",
    "Hamburguesas Mafis S.A. de C.V."    : "Carl's Jr.",
    "Helados Mafis SA de CV"             : "Dairy Queen",
    "Hidrológica Kuale S.A. de C.V."    : "Hidrológica",
    "Tintocinco S.A. de C.V."           : "Tintocinco",
    "Proyectos Sifam S.A. de C.V."      : "Tintocinco",
    "Publipuentes Tamaulipas S.A. de C.V.": "Publipuentes",
    "Mister Motor S.A. de C.V."         : "Mister Motor",
    "Inmobiliaria Erben"                : "Inmobiliaria Erben",
};

function getAlias(companyName) {
    if (!companyName) return null;
    if (COMPANY_ICONS[companyName]) return companyName;
    return COMPANY_ALIASES[companyName] || null;
}

patch(PriorityField.prototype, {
    getCompanyEmoji() {
        const record = this.props.record;
        const companyName = record.data?.company_parent_name ||
                           record.data?.company_id?.[1] || null;
        const alias = getAlias(companyName);
        return alias ? COMPANY_ICONS[alias] : null;
    },

    async onStarClicked(value) {
        await super.onStarClicked(value);
        if (this.props.record.resModel === 'hr.applicant') {
            // Esperar a que se guarde antes de recargar
            await this.props.record.save();
            window.location.reload();
        }
    },
});

PriorityField.template = xml`
<div class="o_priority" role="radiogroup" name="priority" aria-label="Priority">
    <t t-foreach="options" t-as="value" t-key="value">
        <t t-if="!value_first">
            <t t-set="filled" t-value="value_index lte index"/>
            <t t-set="emoji" t-value="getCompanyEmoji()"/>
            <t t-if="props.readonly">
                <span class="o_priority_star"
                    role="radio"
                    tabindex="0"
                    t-att-data-tooltip="getTooltip(value[1])"
                    t-att-aria-checked="value_index === index ? 'true' : 'false'"
                    t-att-aria-label="value[1]"
                    t-att-style="emoji ? 'opacity:' + (filled ? '1' : '0.25') + '; font-size:18px;' : ''">
                    <t t-if="emoji"><t t-out="emoji"/></t>
                    <t t-else=""><i t-att-class="'fa ' + (filled ? 'fa-star' : 'fa-star-o')"/></t>
                </span>
            </t>
            <t t-else="">
                <a href="#"
                    class="o_priority_star"
                    role="radio"
                    tabindex="0"
                    t-att-data-tooltip="getTooltip(value[1])"
                    t-att-aria-checked="value_index === index ? 'true' : 'false'"
                    t-att-aria-label="value[1]"
                    t-att-style="emoji ? 'opacity:' + (filled ? '1' : '0.25') + '; font-size:18px; text-decoration:none;' : ''"
                    t-on-click.prevent.stop="() => this.onStarClicked(value[0])"
                    t-on-mouseenter="() => state.index = value_index"
                    t-on-mouseleave="() => state.index = -1">
                    <t t-if="emoji"><t t-out="emoji"/></t>
                    <t t-else=""><i t-att-class="'fa ' + (filled ? 'fa-star' : 'fa-star-o')"/></t>
                </a>
            </t>
        </t>
    </t>
</div>`;