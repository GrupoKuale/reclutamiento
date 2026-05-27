/** @odoo-module **/

function applyScrollFix() {
    if (!document.querySelector('.o_kanban_view')) return;

    const actionManager = document.querySelector('.o_action_manager');
    const content = document.querySelector('.o_content');

    if (actionManager) actionManager.style.setProperty('overflow', 'visible', 'important');
    if (content) content.style.setProperty('overflow', 'visible', 'important');

    const kanban = document.querySelector('.o_kanban_view');
    if (kanban) {
        kanban.style.setProperty('overflow-x', 'hidden', 'important');
        kanban.style.setProperty('overflow-y', 'auto', 'important');
        kanban.style.setProperty('height', 'calc(100vh - 120px)', 'important');
    }
}

// Espera a que cargue la vista antes de aplicar
setTimeout(() => {
    applyScrollFix();
    // Reaplica solo al cambiar de vista
    document.querySelector('.o_menu_sections')
        ?.addEventListener('click', () => setTimeout(applyScrollFix, 500));
}, 1000);