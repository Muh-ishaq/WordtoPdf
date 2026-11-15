# Paperplane — Word to PDF

A small web app that converts `.doc` and `.docx` files to PDF. The interface is built with HTML, CSS, and vanilla JavaScript; Flask handles uploads and LibreOffice performs the conversion.

## Run with Docker

Install Docker Desktop, then from this folder run:

```powershell
docker compose up --build
```

Open [http://localhost:8000](http://localhost:8000). Stop the app with `Ctrl+C`; run `docker compose down` to remove its container.

If port 8000 is already in use, choose another host port:

```powershell
$env:APP_PORT = "8001"
docker compose up --build
```

Then open [http://localhost:8001](http://localhost:8001).

## Run locally

Install Python dependencies and LibreOffice Writer, then run:

```powershell
python -m pip install -r requirements.txt
python app.py
```

Open [http://localhost:8000](http://localhost:8000). LibreOffice must be available as `soffice` or `libreoffice` on `PATH`.

## Notes

- Accepts `.doc` and `.docx` documents up to 25 MB.
- Each conversion runs in a temporary directory, which is removed after the PDF response is sent.
- Uploads are not saved to persistent storage.
- Run the app tests with `python -m unittest discover -s tests`.
