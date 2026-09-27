FROM python:3.14.7-slim
WORKDIR /usr/src/mc-rcon-api-root
COPY mc_rcon_api/ ./mc_rcon_api/
COPY docker/ ./docker/
COPY poetry.lock ./poetry.lock
COPY pyproject.toml ./pyproject.toml
RUN chmod +x ./docker/*
RUN ./docker/installDeps.sh
CMD ["poetry run start"]
EXPOSE 8000/tcp