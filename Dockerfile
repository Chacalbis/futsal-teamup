FROM python:3.14-slim

WORKDIR /app

RUN pip install --no-cache-dir numpy pyyaml gspread oauth2client colorama

CMD ["python", "script.py"]