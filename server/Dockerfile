FROM python:slim


WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt


COPY ./src/ ./bin

WORKDIR /usr/src/app/bin

CMD [ "python3", "./index.py" ]
