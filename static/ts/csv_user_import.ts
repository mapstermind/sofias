function showStatus(status: HTMLElement, className: string, message: string): void {
  status.hidden = false;
  status.innerHTML = "";

  const item = document.createElement("div");
  item.className = className;
  item.textContent = message;
  status.appendChild(item);
}

function filenameFromResponse(response: Response): string {
  const disposition = response.headers.get("Content-Disposition") || "";
  const match = disposition.match(/filename="?([^"]+)"?/);
  return match?.[1] ?? "user_import_report.csv";
}

function downloadBlob(blob: Blob, filename: string): void {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

function replacePage(html: string): void {
  document.open();
  document.write(html);
  document.close();
}

function setupCSVImportForm(): void {
  const form = document.querySelector<HTMLFormElement>("#csv-import-form");
  const submit = document.querySelector<HTMLInputElement>("#csv-import-submit");
  const status = document.querySelector<HTMLElement>("#import-status");

  if (!form || !submit || !status) return;

  const submitButton = submit;

  function resetSubmit(): void {
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
          showStatus(
            status,
            "success",
            "Importación procesada. El reporte se descargó correctamente."
          );
          resetSubmit();
        });
      })
      .catch((error: unknown) => {
        const message =
          error instanceof Error
            ? error.message
            : "No se pudo completar la importación.";
        showStatus(status, "error", message);
        resetSubmit();
      });
  });
}

document.addEventListener("DOMContentLoaded", setupCSVImportForm);
