import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename

app = Flask(__name__)
MAX_FILE_SIZE = 25 * 1024 * 1024
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE + 1024 * 1024

CONVERSION_TIMEOUT_SECONDS = 90
ALLOWED_EXTENSIONS = {".doc", ".docx"}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.errorhandler(RequestEntityTooLarge)
def handle_upload_too_large(_error):
    return jsonify(error="That file is too large. The maximum size is 25 MB."), 413


@app.get("/")
def home():
    return render_template("index.html")


@app.post("/convert")
def convert_document():
    upload = request.files.get("document")
    if upload is None or not upload.filename:
        return jsonify(error="Choose a Word document to convert."), 400

    safe_name = secure_filename(upload.filename)
    extension = Path(safe_name).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        return jsonify(error="Use a Word document in .doc or .docx format."), 400

    temp_dir = tempfile.TemporaryDirectory(prefix="word-to-pdf-")
    work_dir = Path(temp_dir.name)
    source_path = work_dir / f"source{extension}"
    output_dir = work_dir / "output"
    profile_dir = work_dir / "profile"
    output_dir.mkdir()
    profile_dir.mkdir()
    try:
        upload.save(source_path)
    except OSError:
        temp_dir.cleanup()
        logger.exception("Could not save the uploaded document.")
        return jsonify(error="The uploaded document could not be read. Please try again."), 500

    source_size = source_path.stat().st_size
    if source_size == 0:
        temp_dir.cleanup()
        return jsonify(error="The selected document is empty."), 400
    if source_size > MAX_FILE_SIZE:
        temp_dir.cleanup()
        return jsonify(error="That file is too large. The maximum size is 25 MB."), 413

    converter = shutil.which("soffice") or shutil.which("libreoffice")
    if converter is None:
        temp_dir.cleanup()
        logger.error("LibreOffice executable was not found.")
        return jsonify(error="The document converter is unavailable. Please try again later."), 503

    command = [
        converter,
        "--headless",
        f"-env:UserInstallation={profile_dir.as_uri()}",
        "--convert-to",
        "pdf:writer_pdf_Export",
        "--outdir",
        str(output_dir),
        str(source_path),
    ]

    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=CONVERSION_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        temp_dir.cleanup()
        return jsonify(error="Conversion took too long. Try a smaller or simpler document."), 504
    except OSError:
        temp_dir.cleanup()
        logger.exception("Could not start the document converter.")
        return jsonify(error="The document converter could not be started. Please try again later."), 503

    pdf_path = output_dir / "source.pdf"
    if result.returncode != 0 or not pdf_path.is_file() or pdf_path.stat().st_size == 0:
        temp_dir.cleanup()
        logger.warning("Document conversion failed with exit code %s.", result.returncode)
        return jsonify(error="We couldn't convert this file. Check that it is a valid Word document and try again."), 422

    download_name = f"{Path(safe_name).stem or 'document'}.pdf"
    try:
        response = send_file(
            pdf_path,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=download_name,
        )
    except OSError:
        temp_dir.cleanup()
        logger.exception("Could not prepare the converted PDF response.")
        return jsonify(error="The converted PDF could not be downloaded. Please try again."), 500

    response.call_on_close(temp_dir.cleanup)
    return response


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
