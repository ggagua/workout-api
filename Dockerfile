FROM python:3.12.2-alpine3.18



WORKDIR /app

COPY ./requirements.txt /app

RUN apk add gcc musl-dev libffi-dev
RUN pip install -r requirements.txt

COPY ./app.py /app

CMD ["flask", "run", "--host", "0.0.0.0"]


