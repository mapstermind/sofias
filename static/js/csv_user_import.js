"use strict";
function showStatus(status, className, message) {
    status.hidden = false;
    status.innerHTML = "";
    const item = document.createElement("div");
    item.className = className;
    item.textContent = message;
    status.appendChild(item);
}
function filenameFromResponse(response) {
    var _a;
    const disposition = response.headers.get("Content-Disposition") || "";
    const match = disposition.match(/filename="?([^"]+)"?/);
    return (_a = match === null || match === void 0 ? void 0 : match[1]) !== null && _a !== void 0 ? _a : "user_import_report.csv";
}
function downloadBlob(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
}
function replacePage(html) {
    document.open();
    document.write(html);
    document.close();
}
function setupCSVImportForm() {
    const form = document.querySelector("#csv-import-form");
    const submit = document.querySelector("#csv-import-submit");
    const status = document.querySelector("#import-status");
    if (!form || !submit || !status)
        return;
    const submitButton = submit;
    function resetSubmit() {
        submitButton.disabled = false;
        submitButton.value = "Importar usuarios";
    }
    form.addEventListener("submit", (event) => {
        event.preventDefault();
        submitButton.disabled = true;
        submitButton.value = "Importando...";
        showStatus(status, "info", "CSV enviado. Procesando importación...");
        fetch(form.action || window.location.href, {
            method: "POST",
            body: new FormData(form),
            headers: {
                "X-Requested-With": "XMLHttpRequest",
            },
        })
            .then((response) => {
            const contentType = response.headers.get("Content-Type") || "";
            if (!response.ok) {
                throw new Error("No se pudo completar la importación.");
            }
            if (!contentType.includes("text/csv")) {
                return response.text().then(replacePage);
            }
            return response.blob().then((blob) => {
                downloadBlob(blob, filenameFromResponse(response));
                showStatus(status, "success", "Importación procesada. El reporte se descargó correctamente.");
                resetSubmit();
            });
        })
            .catch((error) => {
            const message = error instanceof Error
                ? error.message
                : "No se pudo completar la importación.";
            showStatus(status, "error", message);
            resetSubmit();
        });
    });
}
document.addEventListener("DOMContentLoaded", setupCSVImportForm);
