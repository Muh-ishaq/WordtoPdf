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

## Deploy to your own Windows machine with GitHub Actions

The workflow in `.github/workflows/deploy.yml` runs for every push to `main`. Build and Test run on GitHub-hosted runners. Deploy waits for both to pass, then updates the Docker Compose app on your Windows machine using a self-hosted runner. No cloud account or Azure secrets are needed.

### 1. Prepare your machine

- Install and start Docker Desktop.
- Make sure ports `8001` (the app) and the GitHub runner's outbound internet access are available. The port can be changed in the workflow's `APP_PORT` value.

### 2. Register a self-hosted runner

1. In GitHub, open this repository's **Settings → Actions → Runners → New self-hosted runner**.
2. Select **Windows** and **x64**.
3. Follow GitHub's displayed commands to download and configure the runner on the machine where the app should run. Run the runner as the same Windows account that can access Docker Desktop.
4. Keep the runner online. For automatic deployment after a reboot, install and start it as a Windows service using GitHub's runner instructions.

### 3. Push to deploy

Push a commit to `main`. In GitHub, open **Actions → Build, test, and deploy** to follow the Build, Test, and Deploy jobs. Deployment runs only after the Docker image builds and all unit tests pass. It runs `docker compose up --build --detach` on your machine and checks that the app responds at `http://localhost:8001`.

The runner executes repository code on your machine, so register it only for a repository and collaborators you trust.

## Notes

- Accepts `.doc` and `.docx` documents up to 25 MB.
- Each conversion runs in a temporary directory, which is removed after the PDF response is sent.
- Uploads are not saved to persistent storage.
- Run the app tests with `python -m unittest discover -s tests`.
