FROM python:3.12-slim

WORKDIR /app

# Install hatch
RUN pip install --no-cache-dir hatch

# Copy project definition first (layer cache)
COPY pyproject.toml .

# Create hatch env (installs all dependencies)
RUN hatch env create

# Copy full source
COPY . .

EXPOSE 8000

CMD ["hatch", "run", "dev"]
