FROM ghcr.io/praekeltfoundation/python-base-nw:3.11-bullseye as build

RUN pip install "poetry==1.5.1"
RUN poetry config virtualenvs.in-project true

# Install just the deps so we use cached layers if they haven't changed
COPY pyproject.toml poetry.lock ./
RUN poetry install --only main --no-root --no-interaction --no-ansi

# Build and install wheels to avoid editable installs
COPY . ./
RUN poetry build && .venv/bin/pip install dist/*.whl


FROM ghcr.io/praekeltfoundation/python-base-nw:3.11-bullseye

# Everything else is installed in the venv, so no reason to copy . anymore
COPY --from=build .venv .venv

ENTRYPOINT [".venv/bin/aaq-sync"]
