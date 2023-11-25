FROM python:3-slim-buster

WORKDIR /usr/src/app
COPY Pipfile Pipfile.lock ${WORKDIR}

RUN pip3 install --upgrade pip && \
    pip3 install pipenv --no-cache-dir && \
    pipenv install --system --deploy && \
    pip3 uninstall -y pipenv virtualenv-clone virtualenv

COPY . ${WORKDIR}

EXPOSE 8000

CMD [ "python3", "./main.py" ]
