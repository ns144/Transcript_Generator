@REM Updating code base
git pull

@REM Starting to listen for HTTP API calls
python -m uvicorn server:app