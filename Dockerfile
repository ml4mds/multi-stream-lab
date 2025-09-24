FROM python:3.11-slim
WORKDIR /app

COPY . .

RUN apt update && apt install -y curl
RUN curl -fLsS https://astral.sh/uv/install.sh | sh
RUN mv $HOME/.local/bin/uv ./
RUN ./uv sync
RUN curl -fLO "https://github.com/ml4mds/multi-stream-lab-frontend/releases/download/v0.1.2/dist.tar.gz"
RUN tar -xzvf dist.tar.gz
RUN mv dist multistreamlab/dist

EXPOSE 8888
CMD ["./uv", "run", "demo.py"]
