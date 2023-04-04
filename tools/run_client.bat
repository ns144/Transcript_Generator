@REM Updating code base
git pull

@REM starting a dramatiq worker
python.exe -m dramatiq worker:broker api.render.tasks api.transcribe.tasks --processes 1 --threads 1