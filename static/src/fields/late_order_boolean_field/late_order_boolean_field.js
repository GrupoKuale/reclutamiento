/** @odoo-module */


import { registry } from "@web/core/registry";
import { BooleanField, booleanField } from "@web/views/fields/boolean/boolean_field";
//import { Component, xml } from "@odoo/owl";

class LateOrderBooleanField extends BooleanField {}

LateOrderBooleanField.template = "reclutamiento__kuale.LateOrderBooleanField";


registry.category("fields").add("late_boolean", {
    ...booleanField,
    component: LateOrderBooleanField,
});



/*
import { Component, xml } from "@odoo/owl";
import { registry } from "@web/core/registry";

export class MyTextField extends Component {
    setup() {
        console.log("Props at setup:", this.props);
        // Verificar si props.value está definido en setup
        if (this.props.value === undefined) {
            console.error("props.value is undefined at setup");
        }
    }


    onChange(ev) {
        const newValue = ev.target.value;
        console.log("New value:", newValue);
        console.log("Props in onChange:", this.props);
        if (this.props.update) {
            this.props.update(newValue);
        } else {
            console.error("Update function is not defined in props");
        }
    }
}

MyTextField.template = xml`
    <div>
        <input t-att-id="props.id"
               class="text-danger"
               t-att-value="props.value || ''"
               t-on-input="onChange" />
        <span t-esc="props.value || 'No value passed'" />
    </div>
`;

MyTextField.props = {
    id: { type: String, optional: true },
    value: { type: String, optional: true },
    update: { type: Function, optional: true },
};

export const cardEditorField = {
    component: MyTextField,
    supportedTypes: ["char"],
}

registry.category("fields").add("my_text_field", cardEditorField);
*/