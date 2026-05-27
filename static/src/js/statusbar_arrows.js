/** @odoo-module **/
import { StatusBarField, statusBarField } from "@web/views/fields/statusbar/statusbar_field";
import { registry } from "@web/core/registry";
import { onMounted, onPatched, useRef } from "@odoo/owl";

function drawBorders(el) {
    if (!el) return;

    const primary = getComputedStyle(document.body)
        .getPropertyValue('--biz-theme-primary-color').trim() || '#5b73e8';

    el.querySelectorAll('.ks-step-wrap').forEach(wrap => {
        const btn = wrap.querySelector('.ks-step');
        if (!btn) return;
        const w = btn.offsetWidth;
        const h = btn.offsetHeight;
        if (!w || !h) return;
        const tip = 12;
        const isCurrent = btn.classList.contains('ks-step-current');

        let svg = wrap.querySelector('.ks-border-svg');
        if (!svg) {
            svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            svg.classList.add('ks-border-svg');
            wrap.insertBefore(svg, btn);
        }
        svg.setAttribute('width', w);
        svg.setAttribute('height', h);
        svg.setAttribute('viewBox', `0 0 ${w} ${h}`);
        svg.style.cssText = `position:absolute;top:0;left:0;width:${w}px;height:${h}px;pointer-events:none;z-index:0;overflow:visible;`;

        const points = `1,1 ${w-tip},1 ${w-1},${h/2} ${w-tip},${h-1} 1,${h-1} ${tip+1},${h/2}`;

        let poly = svg.querySelector('polygon');
        if (!poly) {
            poly = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
            svg.appendChild(poly);
        }
        poly.setAttribute('points', points);

        if (isCurrent) {
            poly.setAttribute('fill', primary);
            poly.setAttribute('stroke', primary);
            poly.setAttribute('stroke-width', '1');
        } else {
            poly.setAttribute('fill', 'white');
            poly.setAttribute('stroke', primary);
            poly.setAttribute('stroke-width', '1.5');
        }
    });
}

export class KsStatusBarField extends StatusBarField {
    static template = "reclutamiento__kuale.StatusBarField";

    setup() {
        super.setup();
        const rootRef = useRef("root");
        onMounted(() => {
            drawBorders(rootRef.el);
        });
        onPatched(() => {
            drawBorders(rootRef.el);
        });
    }

    adjustVisibleItems() {}
}

export const ksStatusBarField = {
    ...statusBarField,
    component: KsStatusBarField,
};

registry.category("fields").add("statusbar", ksStatusBarField, { force: true });