FROM python:slim


WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt


COPY ./src/ ./bin
COPY ./drivers ./drivers

WORKDIR /usr/src/app/bin

CMD [ "python3", "./index.py" ]
