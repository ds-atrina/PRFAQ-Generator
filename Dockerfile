FROM python:3.12-slim

WORKDIR /app

COPY rv.txt /app/requirements.txt
RUN pwd
RUN ls -l

RUN pip install -r requirements.txt

COPY . /app

EXPOSE 8082

ENTRYPOINT ["python", "api.py"]