/** @odoo-module **/
import { FormRenderer } from "@web/views/form/form_renderer";
import { patch } from "@web/core/utils/patch";
import { onMounted } from "@odoo/owl";

patch(FormRenderer.prototype, {
    setup() {
        super.setup();
        onMounted(() => {
            setTimeout(() => {
                this._adjustChips();
                const container = document.querySelector('#chips_container');
                if (container) {
                    const observer = new ResizeObserver(() => {
                        this._adjustChips();
                    });
                    observer.observe(container.parentElement || container);
                }
                window.addEventListener('resize', () => {
                    setTimeout(() => this._adjustChips(), 100);
                });
            }, 500);
        });
    },

    _adjustChips() {
        const container = document.querySelector('#chips_container');
        if (!container) return;

        const chips = Array.from(container.children).filter(el => 
            el.tagName === 'SPAN' && el.style.borderRadius
        );
        if (!chips.length) return;

        // Siempre tamaño legible
        chips.forEach(chip => {
            chip.style.fontSize = '11px';
            chip.style.padding = '2px 8px';
        });

        const containerWidth = container.offsetWidth;
        const totalWidth = chips.reduce((acc, chip) => acc + chip.offsetWidth + 4, 0);

        if (totalWidth <= containerWidth) {
            container.style.flexWrap = 'nowrap';
            container.style.justifyContent = 'space-evenly';
            container.style.gap = '0px';
            chips.forEach(chip => {
                chip.style.flexGrow = '0';
                chip.style.textAlign = '';
                chip.style.justifyContent = '';
            });
        } else {
            container.style.flexWrap = 'wrap';
            container.style.justifyContent = 'space-evenly';
            container.style.gap = '0px';
            container.style.rowGap = '6px';
            chips.forEach(chip => {
                chip.style.flexGrow = '0';
                chip.style.textAlign = '';
                chip.style.justifyContent = '';
            });
        }
    },
});