FROM python:3.10

RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y


WORKDIR /usr/src/app
COPY . /usr/src/app/client

RUN pip install -r ./client/requirements.txt

EXPOSE 80

CMD ["uvicorn", "client.main:app", "--reload", "--host", "localhost", "--port", "80"]