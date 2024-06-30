FROM debian:11-slim AS builder

RUN apt-get update && apt-get install -y \
    zlib1g \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 下载最新 release 的 main 文件
RUN curl -L -o main https://github.com/TheValkyrja/Anthropic2Vertex/releases/latest/download/main && \
    chmod 755 main

FROM gcr.io/distroless/cc-debian11

WORKDIR /app

COPY --from=builder /lib/x86_64-linux-gnu/libz.so.1 /lib/x86_64-linux-gnu/libz.so.1

# 从 builder 阶段复制下载的 main 文件
COPY --from=builder /main .

COPY model_mapping.json .
COPY .env .
COPY auth/auth.json auth/

ENV DOCKER_ENV=true

CMD ["./main"]