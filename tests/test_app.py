import io
import subprocess
import unittest
from unittest.mock import patch

from app import app
from flask import Response


class ConverterAppTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def tearDown(self):
        app.config["TESTING"] = False

    def test_homepage_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Word in.", response.data)

    def test_rejects_unsupported_file_type(self):
        response = self.client.post(
            "/convert",
            data={"document": (io.BytesIO(b"not a word file"), "notes.txt")},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Word document", response.json["error"])

    def test_rejects_missing_file(self):
        response = self.client.post("/convert", data={})
        self.assertEqual(response.status_code, 400)
        self.assertIn("Choose a Word document", response.json["error"])

    def test_rejects_empty_file(self):
        response = self.client.post(
            "/convert",
            data={"document": (io.BytesIO(b""), "empty.docx")},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("document is empty", response.json["error"])

    @patch("app.shutil.which", return_value="/usr/bin/soffice")
    @patch("app.subprocess.run")
    @patch("app.send_file")
    def test_converts_docx_and_returns_download(self, send_pdf, run, _which):
        def create_pdf(command, **_kwargs):
            output_dir = command[command.index("--outdir") + 1]
            with open(f"{output_dir}/source.pdf", "wb") as pdf:
                pdf.write(b"%PDF-1.4 test")
            return subprocess.CompletedProcess(command, 0)

        def read_pdf(path, **kwargs):
            with open(path, "rb") as pdf:
                content = pdf.read()
            return Response(
                content,
                mimetype=kwargs["mimetype"],
                headers={"Content-Disposition": f'attachment; filename={kwargs["download_name"]}'},
            )

        run.side_effect = create_pdf
        send_pdf.side_effect = read_pdf
        response = self.client.post(
            "/convert",
            data={"document": (io.BytesIO(b"docx bytes"), "my report.docx")},
            buffered=True,
        )
        pdf_bytes = response.data
        response.close()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/pdf")
        self.assertEqual(response.headers["Content-Disposition"], "attachment; filename=my_report.pdf")
        self.assertEqual(pdf_bytes, b"%PDF-1.4 test")
        run.assert_called_once()
        self.assertNotIn("shell", run.call_args.kwargs)
        send_pdf.assert_called_once()
        self.assertEqual(send_pdf.call_args.kwargs["download_name"], "my_report.pdf")

    @patch("app.shutil.which", return_value=None)
    def test_reports_missing_converter(self, _which):
        response = self.client.post(
            "/convert",
            data={"document": (io.BytesIO(b"docx bytes"), "report.docx")},
        )
        self.assertEqual(response.status_code, 503)
        self.assertIn("converter is unavailable", response.json["error"])

    @patch("app.shutil.which", return_value="/usr/bin/soffice")
    @patch("app.subprocess.run", side_effect=subprocess.TimeoutExpired("soffice", 90))
    def test_reports_conversion_timeout(self, _run, _which):
        response = self.client.post(
            "/convert",
            data={"document": (io.BytesIO(b"docx bytes"), "report.docx")},
        )
        self.assertEqual(response.status_code, 504)
        self.assertIn("took too long", response.json["error"])


if __name__ == "__main__":
    unittest.main()
