FROM python:3.9-slim

WORKDIR /app

RUN pip install --no-cache-dir numpy pyyaml gspread oauth2client colorama

CMD ["python", "script.py"]