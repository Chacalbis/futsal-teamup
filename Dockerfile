FROM python:3.14-slim

WORKDIR /app

RUN pip install --no-cache-dir numpy pyyaml gspread oauth2client colorama zulip requests

CMD ["python", "script.py"]