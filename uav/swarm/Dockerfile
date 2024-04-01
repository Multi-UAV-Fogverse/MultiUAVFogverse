FROM python:3.10
RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y
COPY fogverse ./fogverse
COPY uav/swarm ./swarm
RUN pip install -r ./swarm/requirements.txt
CMD [ "python", "-m", "swarm" ]