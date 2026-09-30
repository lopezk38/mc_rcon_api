FROM python:3.14.7-slim
WORKDIR /usr/src/mc-rcon-api-root
COPY mc_rcon_api/ ./mc_rcon_api/
COPY docker/ ./docker/
COPY poetry.lock ./poetry.lock
COPY pyproject.toml ./pyproject.toml
COPY README.md ./README.md
RUN chmod +x ./docker/*
RUN ./docker/installDeps.sh
ENV PATH="$PATH:/root/.local/bin"
CMD poetry run start
EXPOSE 8000/tcp
