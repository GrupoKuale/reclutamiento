/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { BooleanFavoriteField } from "@web/views/fields/boolean_favorite/boolean_favorite_field";
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
    "Carl's"                               : "Carl's Jr.",
    "Hamburguesas Mafis S.A. de C.V."     : "Carl's Jr.",
    "Helados Mafis SA de CV"              : "Dairy Queen",
    "Hidrológica Kuale S.A. de C.V."     : "Hidrológica",
    "Tintocinco S.A. de C.V."            : "Tintocinco",
    "Proyectos Sifam S.A. de C.V."       : "Tintocinco",
    "Publipuentes Tamaulipas S.A. de C.V.": "Publipuentes",
    "Mister Motor S.A. de C.V."          : "Mister Motor",
    "Inmobiliaria Erben"                  : "Inmobiliaria Erben",
};

function getCompanyEmoji(record) {
    if (!record || record.resModel !== "hr.job") return null;
    const branchCompany = record.data?.branch_company_id;
    const companyName = Array.isArray(branchCompany)
        ? branchCompany[1]
        : (branchCompany?.display_name || null);
    if (!companyName) return null;
    const canon = COMPANY_ICONS[companyName]
        ? companyName
        : COMPANY_ALIASES[companyName] || null;
    return canon ? COMPANY_ICONS[canon] : null;
}

patch(BooleanFavoriteField.prototype, {
    getCompanyEmoji() {
        return getCompanyEmoji(this.props.record);
    },
});

BooleanFavoriteField.template = xml`
<div class="o_favorite" t-on-click.prevent.stop="update" style="cursor:pointer;">
    <a href="#">
        <t t-set="emoji" t-value="getCompanyEmoji()"/>
        <t t-if="emoji">
            <span t-att-style="'font-size:18px; line-height:1; opacity:' + (props.record.data[props.name] ? '1' : '0.4')">
                <t t-out="emoji"/>
            </span>
        </t>
        <t t-else="">
            <t t-if="props.record.data[props.name]">
                <i class="fa fa-star me-1" role="img" title="Remove from Favorites" aria-label="Remove from Favorites"/>
                <t t-if="!props.noLabel">Remove from Favorites</t>
            </t>
            <t t-else="">
                <i class="fa fa-star-o me-1" role="img" title="Add to Favorites" aria-label="Add to Favorites"/>
                <t t-if="!props.noLabel">Add to Favorites</t>
            </t>
        </t>
    </a>
</div>`;