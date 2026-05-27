/** @odoo-module */
import {FormController} from "@web/views/form/form_controller";
import {formView} from '@web/views/form/form_view';
import {registry} from '@web/core/registry';
import {useService} from "@web/core/utils/hooks";

export class GoBackFormController extends FormController {
    setup() {
        super.setup();
        this.actionService = useService("action");
    }

    GoBack() {
        window.history.back()
    }
}

GoBackFormController.template = 'go_back_button.FormView.Buttons';
export const modelInfoView = {...formView, Controller: GoBackFormController,};
registry.category("views").add("go_back_button", modelInfoView);