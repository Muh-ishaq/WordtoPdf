const form = document.querySelector("#upload-form");
const input = document.querySelector("#document-input");
const dropZone = document.querySelector("#drop-zone");
const dropTitle = document.querySelector("#drop-title");
const dropSubtitle = document.querySelector("#drop-subtitle");
const selectedFile = document.querySelector("#selected-file");
const fileName = document.querySelector("#file-name");
const fileSize = document.querySelector("#file-size");
const convertButton = document.querySelector("#convert-button");
const buttonLabel = document.querySelector("#button-label");
const buttonArrow = document.querySelector("#button-arrow");
const spinner = document.querySelector("#spinner");
const statusMessage = document.querySelector("#status-message");

const allowedExtensions = [".doc", ".docx"];
let currentFile = null;

function isSupported(file) {
  return allowedExtensions.some((extension) => file.name.toLowerCase().endsWith(extension));
}

function formatBytes(bytes) {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function showStatus(message, success = false) {
  statusMessage.textContent = message;
  statusMessage.classList.toggle("is-success", success);
}

function selectFile(file) {
  showStatus("");
  if (!file) return;
  if (!isSupported(file)) {
    showStatus("Please choose a .doc or .docx file.");
    return;
  }
  if (file.size > 25 * 1024 * 1024) {
    showStatus("That file is too large. The maximum size is 25 MB.");
    return;
  }
  currentFile = file;
  input.value = "";
  dropZone.hidden = true;
  selectedFile.hidden = false;
  fileName.textContent = file.name;
  fileSize.textContent = formatBytes(file.size);
  convertButton.disabled = false;
}

function clearFile() {
  currentFile = null;
  selectedFile.hidden = true;
  dropZone.hidden = false;
  convertButton.disabled = true;
  showStatus("");
}

function setLoading(loading) {
  convertButton.disabled = loading || !currentFile;
  buttonLabel.textContent = loading ? "Making your PDF..." : "Make it a PDF";
  buttonArrow.hidden = loading;
  spinner.hidden = !loading;
}

input.addEventListener("change", () => selectFile(input.files?.[0]));
document.querySelector("#remove-file").addEventListener("click", clearFile);

dropZone.addEventListener("keydown", (event) => {
  if (event.key === "Enter" || event.key === " ") {
    event.preventDefault();
    input.click();
  }
});

for (const eventName of ["dragenter", "dragover"]) {
  dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropZone.classList.add("is-dragging");
  });
}

for (const eventName of ["dragleave", "drop"]) {
  dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropZone.classList.remove("is-dragging");
  });
}

dropZone.addEventListener("drop", (event) => selectFile(event.dataTransfer.files?.[0]));

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!currentFile) return;

  const data = new FormData();
  data.append("document", currentFile);
  setLoading(true);
  showStatus("");

  try {
    const response = await fetch("/convert", { method: "POST", body: data });
    if (!response.ok) {
      const result = await response.json();
      throw new Error(result.error || "Something went wrong. Please try again.");
    }

    const pdf = await response.blob();
    const url = URL.createObjectURL(pdf);
    const link = document.createElement("a");
    const contentDisposition = response.headers.get("Content-Disposition") || "";
    const fileNameMatch = contentDisposition.match(/filename="?([^";]+)"?/i);
    link.href = url;
    link.download = fileNameMatch?.[1] || `${currentFile.name.replace(/\.(docx?)$/i, "")}.pdf`;
    document.body.append(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    showStatus("Your PDF is ready and downloading.", true);
  } catch (error) {
    showStatus(error.message || "Something went wrong. Please try again.");
  } finally {
    setLoading(false);
  }
});
