window.nextSection = window.nextSection || function () {};
window.prevSection = window.prevSection || function () {};
function initKualeApplyNavigation() {
    const pageRoot = document.querySelector(".kuale-apply");
    if (!pageRoot) return;
    const form = pageRoot.querySelector("form#hr_recruitment_form2");
    const sections = Array.from(pageRoot.querySelectorAll(".form-section"));
    const progressBar = pageRoot.querySelector("#progressBar");
    if (!form || sections.length === 0) return;
    let currentSection = 0;
    function setHiddenCsvValue(hiddenId, values) {
        const hidden = pageRoot.querySelector(`#${hiddenId}`);
        if (!hidden) return;
        hidden.value = (values || [])
            .filter((v) => v !== undefined && v !== null && String(v).trim() !== "")
            .join(",");
    }
    function syncCsvFields() {
        const reqValues = Array.from(pageRoot.querySelectorAll(".kuale-requisition-checkbox:checked")).map((el) => el.value);
        setHiddenCsvValue("kuale_requisition_id", reqValues);
        const identValues = Array.from(pageRoot.querySelectorAll(".identification-checkbox:checked")).map((el) => el.value);
        setHiddenCsvValue("kuale_identification_options_ids", identValues);
        const compSelect = pageRoot.querySelector("#competencies_ids_select");
        if (compSelect) {
            const compValues = Array.from(compSelect.selectedOptions || []).map((o) => o.value);
            setHiddenCsvValue("kuale_competencies_ids", compValues);
        }
        const abilitySelect = pageRoot.querySelector("#ability_ids_select");
        if (abilitySelect) {
            const abilityValues = Array.from(abilitySelect.selectedOptions || []).map((o) => o.value);
            setHiddenCsvValue("kuale_ability_ids", abilityValues);
        }
    }
    function updateProgressBar(index) {
        if (!progressBar) return;
        const totalSteps = sections.length;
        if (!totalSteps) return;
        const percentage = ((index + 1) / totalSteps) * 100;
        progressBar.style.width = `${percentage}%`;
    }
    function showSection(index) {
        sections.forEach((section, i) => {
            section.classList.toggle("d-none", i !== index);
        });
        updateProgressBar(index);
    }
    function isFieldFilled(field, scopeEl) {
        if (!field) return true;
        const tag = (field.tagName || "").toLowerCase();
        const type = (field.type || "").toLowerCase();
        if (type === "hidden") {
            return !!(field.value && String(field.value).trim());
        }
        if (type === "radio") {
            const name = field.name;
            if (!name) return true;
            const group = scopeEl.querySelectorAll(`input[type="radio"][name="${name}"]`);
            return Array.from(group).some((r) => r.checked);
        }
        if (type === "checkbox") return !!field.checked;
        if (tag === "select" && field.multiple) {
            return field.selectedOptions && field.selectedOptions.length > 0;
        }
        return !!(field.value && String(field.value).trim());
    }
    function getFieldLabel(field, scope) {
        if (field.id === "schedule_filled") return "Horario";
        if (field.id === "experience_filled") return "Agregar experiencia laboral";
        if (field.id === "recommendation_letter") return "Carta de recomendación";
        if (field.id === "bank_filled") return "Cuenta bancaria";
        if (field.id === "beneficiary_filled") return "Beneficiario"; 
        if (field.id) {
            const label = scope.querySelector(`label[for="${field.id}"]`);
            if (label) {
                const content = label.querySelector(".s_website_form_label_content");
                return (content ? content.textContent : label.textContent).trim();
            }
        }
        const parentLabel = field.closest("label");
        if (parentLabel) {
            const content = parentLabel.querySelector(".s_website_form_label_content");
            return (content ? content.textContent : parentLabel.textContent).trim();
        }
        let prev = field.previousElementSibling;
        while (prev) {
            if (prev.tagName && prev.tagName.toLowerCase() === "label") {
                const content = prev.querySelector(".s_website_form_label_content");
                return (content ? content.textContent : prev.textContent).trim();
            }
            prev = prev.previousElementSibling;
        }
        const container = field.closest(".col-12, .col-md-6, .col-md-4, .col-md-3, .col-xl-4, .col-xl-3, .col-xl-2, .col-auto");
        if (container) {
            const label = container.querySelector("label");
            if (label) {
                const content = label.querySelector(".s_website_form_label_content");
                return (content ? content.textContent : label.textContent).trim();
            }
        }
        return field.name || field.id || "Campo requerido";
    }
    function setBorderError(el) {
        if (!el) return;
        el.setAttribute("data-kuale-error", "1");
        el.style.setProperty("border", "2px solid #FFA500", "important");
        el.style.setProperty("border-radius", "4px", "important");
        el.style.setProperty("outline", "none", "important");
    }
    function clearBorderError(el) {
        if (!el) return;
        el.removeAttribute("data-kuale-error");
        el.style.removeProperty("border");
        el.style.removeProperty("border-radius");
        el.style.removeProperty("outline");
        if (el.classList.contains("form-control") || el.classList.contains("s_website_form_input")) {
            el.style.setProperty("border", "1px solid #ced4da", "important");
        } else if (el.classList.contains("kuale-state-dropdown__trigger")) {
            el.style.setProperty("border", "1.5px solid var(--kuale-border)", "important");
            el.style.setProperty("border-radius", "var(--kuale-radius)", "important");
        } else if (el.classList.contains("kuale-file-upload")) {
            el.style.setProperty("border", "2px dashed var(--kuale-border)", "important");
            el.style.setProperty("border-radius", "var(--kuale-radius)", "important");
        }
    }
    function clearTagsContainerError(el) {
        if (!el) return;
        el.removeAttribute("data-kuale-error");
        el.style.removeProperty("border");
        el.style.removeProperty("border-radius");
        el.style.removeProperty("outline");
        el.style.setProperty("border", "1.5px solid var(--kuale-border)", "important");
        el.style.setProperty("border-radius", "var(--kuale-radius)", "important");
    }
    function clearBtnError(btn) {
        if (!btn) return;
        btn.removeAttribute("data-kuale-error");
        btn.style.setProperty("border", "none", "important");
        btn.style.setProperty("border-radius", "999px", "important");
        btn.style.removeProperty("outline");
    }
    function applyErrorBorder(field, scope) {
        const id = field.id;
        if (id === "experience_filled") {
            const btn = pageRoot.querySelector("#btn_add_experience");
            if (btn) {
                btn.style.setProperty("border", "2px solid #FFA500", "important");
                btn.style.setProperty("border-radius", "999px", "important");
            }
            return;
        }
        if (id === "ine_document") {
            setBorderError(scope.querySelector("#ine_upload_box"));
            return;
        }
        if (id === "rfc_files") {
            setBorderError(scope.querySelector("#rfc_upload_box"));
            return;
        }
        if (id === "nss_files") {
            setBorderError(scope.querySelector("#nss_upload_box"));
            return;
        }
        if (id === "driver_files") {
            setBorderError(scope.querySelector("#driver_upload_box"));
            return;
        }
        if (id === "colony") {
            setBorderError(pageRoot.querySelector("#colonyInput"));
            return;
        }
        if (id === "schedule_filled") {
            const btn = pageRoot.querySelector("#open_schedule_modal");
            if (btn) {
                btn.style.setProperty("border", "2px solid #FFA500", "important");
                btn.style.setProperty("border-radius", "999px", "important");
            }
            return;
        }
        if (id === "bank_filled") {
            const btn = pageRoot.querySelector("#btn_add_bank");
            if (btn) {
                btn.style.setProperty("border", "2px solid #FFA500", "important");
                btn.style.setProperty("border-radius", "999px", "important");
            }
            return;
        }
        if (id === "beneficiary_filled") {
            const btn = pageRoot.querySelector("#btn_add_beneficiary");
            if (btn) {
                btn.style.setProperty("border", "2px solid #FFA500", "important");
                btn.style.setProperty("border-radius", "999px", "important");
            }
            return;
        }
        if (id === "recruitment6") {
            setBorderError(pageRoot.querySelector("#curriculum_upload_box"));
            return;
        }
        if (field.type === "hidden") {
            const container = field.closest(".col-12, .col-md-6, .col-xl-4, .col-auto, .col-md-4");
            if (container) {
                setBorderError(container.querySelector(".kuale-state-dropdown__trigger"));
            }
            return;
        }
        setBorderError(field);
    }
    function clearErrorBorder(field, scope) {
        const id = field.id;
        if (id === "experience_filled") {
            clearBtnError(pageRoot.querySelector("#btn_add_experience"));
            return;
        }
        if (id === "ine_document") {
            clearBorderError(scope ? scope.querySelector("#ine_upload_box") : pageRoot.querySelector("#ine_upload_box"));
            return;
        }
        if (id === "rfc_files") {
            clearBorderError(scope ? scope.querySelector("#rfc_upload_box") : pageRoot.querySelector("#rfc_upload_box"));
            return;
        }
        if (id === "nss_files") {
            clearBorderError(scope ? scope.querySelector("#nss_upload_box") : pageRoot.querySelector("#nss_upload_box"));
            return;
        }
        if (id === "driver_files") {
            clearBorderError(scope ? scope.querySelector("#driver_upload_box") : pageRoot.querySelector("#driver_upload_box"));
            return;
        }
        if (id === "colony") {
            clearBorderError(pageRoot.querySelector("#colonyInput"));
            return;
        }
        if (id === "schedule_filled") {
            clearBtnError(pageRoot.querySelector("#open_schedule_modal"));
            return;
        }
        if (id === "recruitment6") {
            clearBorderError(pageRoot.querySelector("#curriculum_upload_box"));
            return;
        }
        if (id === "bank_filled") {
            clearBtnError(pageRoot.querySelector("#btn_add_bank"));
            return;
        }
        if (id === "beneficiary_filled") {
            clearBtnError(pageRoot.querySelector("#btn_add_beneficiary"));
            return;
        }
        if (field.type === "hidden") {
            const container = field.closest(".col-12, .col-md-6, .col-xl-4, .col-auto, .col-md-4");
            if (container) {
                clearBorderError(container.querySelector(".kuale-state-dropdown__trigger"));
            }
            return;
        }
        clearBorderError(field);
    }
    function validateRequiredFields() {
        const scope = sections[currentSection];
        const requiredFields = Array.from(scope.querySelectorAll("[required]"));
        let allFieldsValid = true;
        const missingLabels = [];
        const seenNames = new Set();

        // ── Validación de sucursales ──────────────────────────────
        const branchTagsContainer = scope.querySelector("#branch_tags");
        if (branchTagsContainer) {
            const hasBranches = Object.keys(selectedBranches).length > 0;
            if (!hasBranches) {
                allFieldsValid = false;
                setBorderError(branchTagsContainer);
                if (!seenNames.has("branch")) {
                    seenNames.add("branch");
                    missingLabels.push("Sucursales disponibles");
                }
            } else {
                clearTagsContainerError(branchTagsContainer);
            }
        }

        const isExperienceSection = scope.querySelector("#experience_filled") !== null;
        if (isExperienceSection) {
            const expFilled = scope.querySelector("#experience_filled");
            if (expFilled !== null) {
                const expFieldsVisible = pageRoot.querySelector("#experience_fields");
                const isVisible = expFieldsVisible && expFieldsVisible.style.display !== "none";
                if (isVisible) {
                    const ok = !!(expFilled.value && String(expFilled.value).trim());
                    const btn = pageRoot.querySelector("#btn_add_experience");
                    if (!ok) {
                        allFieldsValid = false;
                        if (btn) {
                            btn.style.setProperty("border", "2px solid #FFA500", "important");
                            btn.style.setProperty("border-radius", "999px", "important");
                        }
                        if (!seenNames.has("experience_filled")) {
                            seenNames.add("experience_filled");
                            missingLabels.push("Agregar experiencia laboral");
                        }
                    } else {
                        clearBtnError(btn);
                    }
                }
            }
        }
        requiredFields.forEach((field) => {
            if (field.id === "experience_filled") return;
            if (field.id === "actual_benefits") return;
            if (field.id === "recommendation_letter") return;
            if (field.id === "imss_clinic") return;
            const ok = isFieldFilled(field, scope);
            field.classList.remove("is-invalid");
            clearErrorBorder(field, scope);
            if (!ok) {
                allFieldsValid = false;
                applyErrorBorder(field, scope);
                const name = field.name || field.id;
                if (!seenNames.has(name)) {
                    seenNames.add(name);
                    const label = getFieldLabel(field, scope);
                    if (label) missingLabels.push(label);
                }
            }
        });
        if (!allFieldsValid) {
            const alertModal = pageRoot.querySelector("#alertModal");
            const modalBody = alertModal ? alertModal.querySelector(".modal-body") : null;
            if (modalBody) {
                let html = "<p>Por favor, completa los siguientes campos antes de continuar:</p><ul style='text-align:left; margin-top:8px;'>";
                missingLabels.forEach(function (lbl) {
                    html += `<li style="margin-bottom:4px;"><strong>${lbl}</strong></li>`;
                });
                html += "</ul>";
                modalBody.innerHTML = html;
            }
            if (alertModal && window.$ && typeof window.$(alertModal).modal === "function") {
                window.$(alertModal).modal("show");
                const acceptBtn = alertModal.querySelector("#acceptAlertModal");
                if (acceptBtn) {
                    const newBtn = acceptBtn.cloneNode(true);
                    acceptBtn.parentNode.replaceChild(newBtn, acceptBtn);
                    newBtn.addEventListener("click", function () {
                        window.$(alertModal).modal("hide");
                    });
                }
            }
        }
        return allFieldsValid;
    }
    pageRoot.addEventListener("input", function (e) {
        if (e.target && e.target.style) {
            if (e.target.id === "colonyInput" || e.target.id === "colonyFiscalInput") return;
            clearBorderError(e.target);
        }
    });
    pageRoot.addEventListener("change", function (e) {
        if (e.target && e.target.style) {
            clearBorderError(e.target);
            if (e.target.type === "hidden") {
                clearErrorBorder(e.target, null);
            }
        }
    });
    const ineDocInput = pageRoot.querySelector("#ine_document");
    if (ineDocInput) {
        ineDocInput.addEventListener("change", function () {
            clearBorderError(pageRoot.querySelector("#ine_upload_box"));
        });
    }
    const rfcFilesInput = pageRoot.querySelector("#rfc_files");
    if (rfcFilesInput) {
        rfcFilesInput.addEventListener("change", function () {
            clearBorderError(pageRoot.querySelector("#rfc_upload_box"));
        });
    }
    const nssFilesInput = pageRoot.querySelector("#nss_files");
    if (nssFilesInput) {
        nssFilesInput.addEventListener("change", function () {
            clearBorderError(pageRoot.querySelector("#nss_upload_box"));
        });
    }
    const driverFilesInput = pageRoot.querySelector("#driver_files");
    if (driverFilesInput) {
        driverFilesInput.addEventListener("change", function () {
            clearBorderError(pageRoot.querySelector("#driver_upload_box"));
        });
    }
    const curriculumInput = pageRoot.querySelector("#recruitment6");
    if (curriculumInput) {
        curriculumInput.addEventListener("change", function () {
            clearBorderError(pageRoot.querySelector("#curriculum_upload_box"));
        });
    }
    const scheduleFilledInput = pageRoot.querySelector("#schedule_filled");
    if (scheduleFilledInput) {
        const observer = new MutationObserver(function () {
            if (scheduleFilledInput.value) {
                const btn = pageRoot.querySelector("#open_schedule_modal");
                if (btn) { clearBtnError(btn); }
            }
        });
        observer.observe(scheduleFilledInput, { attributes: true, attributeFilter: ["value"] });
        scheduleFilledInput.addEventListener("change", function () {
            if (scheduleFilledInput.value) {
                const btn = pageRoot.querySelector("#open_schedule_modal");
                if (btn) { clearBtnError(btn); }
            }
        });
    }
    function watchDropdownHidden(hiddenId) {
        const hiddenEl = pageRoot.querySelector("#" + hiddenId);
        if (!hiddenEl) return;
        function clearTrigger() {
            if (hiddenEl.value) {
                const container = hiddenEl.closest(".col-12, .col-md-6, .col-xl-4, .col-auto, .col-md-4");
                if (container) {
                    clearBorderError(container.querySelector(".kuale-state-dropdown__trigger"));
                }
            }
        }
        const observer = new MutationObserver(clearTrigger);
        observer.observe(hiddenEl, { attributes: true, attributeFilter: ["value"] });
        hiddenEl.addEventListener("change", clearTrigger);
    }
    watchDropdownHidden("state_birth_Select");
    watchDropdownHidden("birthplace_select");
    watchDropdownHidden("lives_with_hidden");
    watchDropdownHidden("children_hidden");
    watchDropdownHidden("ine_type_selected");
    watchDropdownHidden("previous_experience_hidden");
    function watchColonyHidden() {
        const hiddenEl = pageRoot.querySelector("#colony");
        const colonyInput = pageRoot.querySelector("#colonyInput");
        if (!hiddenEl || !colonyInput) return;
        function clearColonyBorder() {
            if (hiddenEl.value && hiddenEl.value.trim()) {
                clearBorderError(colonyInput);
            }
        }
        const observer = new MutationObserver(clearColonyBorder);
        observer.observe(hiddenEl, { attributes: true, attributeFilter: ["value"] });
        hiddenEl.addEventListener("change", clearColonyBorder);
        colonyInput.addEventListener("input", function () {
            if (colonyInput.value && colonyInput.value.trim()) {
                clearBorderError(colonyInput);
            }
        });
    }
    watchColonyHidden();
    function watchValueAndClearBorder(fieldId) {
        const field = pageRoot.querySelector("#" + fieldId);
        if (!field) return;
        const descriptor = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value");
        Object.defineProperty(field, "value", {
            get: function () { return descriptor.get.call(this); },
            set: function (v) {
                descriptor.set.call(this, v);
                if (v) {
                    clearBorderError(this);
                }
            },
            configurable: true
        });
    }
    watchValueAndClearBorder("birthdate");
    watchValueAndClearBorder("age");
    watchValueAndClearBorder("state");
    watchValueAndClearBorder("municipality");
    window.nextSection = function () {
        syncCsvFields();
        if (validateRequiredFields() && currentSection < sections.length - 1) {
            currentSection++;
            showSection(currentSection);
            const target = pageRoot || document.body;
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    };
    window.prevSection = function () {
        if (currentSection > 0) {
            currentSection--;
            showSection(currentSection);
            const target = pageRoot || document.body;
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    };
    form.setAttribute("novalidate", "");
    form.addEventListener("submit", function (e) {
        syncCsvFields();
        if (!validateRequiredFields()) {
            e.preventDefault();
        }
    });
    pageRoot
        .querySelectorAll(".kuale-requisition-checkbox, .identification-checkbox, #competencies_ids_select, #ability_ids_select")
        .forEach((el) => el.addEventListener("change", syncCsvFields));
    syncCsvFields();
    showSection(currentSection);
    
    // Quitar required de recommendation_letter cada vez que Odoo lo agregue
    function removeRecRequired() {
        var rec = document.getElementById('recommendation_letter');
        if (rec && rec.hasAttribute('required')) {
            rec.removeAttribute('required');
        }
    }
    removeRecRequired();
    setInterval(removeRecRequired, 300);
}
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initKualeApplyNavigation);
} else {
    initKualeApplyNavigation();
}