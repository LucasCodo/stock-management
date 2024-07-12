FROM python:3.11
LABEL authors="luss1"

WORKDIR /code

COPY . /code/app

RUN pip install --no-cache-dir --upgrade -r /code/app/requirements.txt

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]