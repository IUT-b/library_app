FROM python:3.10.1

RUN apt-get update && apt-get install -y sqlite3 && apt-get install -y libsqlite3-dev && apt-get install -y libgl1-mesa-dev

WORKDIR /usr/src/

COPY ./apps /usr/src/apps
COPY ./local.sqlite /usr/src/local.sqlite
COPY ./requirements.txt /usr/src/requirements.txt
COPY ./model.pt /usr/src/model.pt

RUN pip install --upgrade pip

RUN pip install torch==1.11.0+cpu torchvision==0.12.0+cpu torchaudio==0.11.0 -f https://download.pytorch.org/whl/torch_stable.html

RUN pip install -r requirements.txt

RUN echo "building..."

ENV FLASK_APP "apps.app:create_app('local')"
ENV IMAGE_URL "/storage/images/"

EXPOSE 5000

CMD ["flask","run","-h","0.0.0.0"]