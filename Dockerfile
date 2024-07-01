# syntax=docker/dockerfile:1

FROM debian:11-slim AS builder

ARG TARGETARCH

RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 使用单一链接下载对应架构的可执行文件
RUN curl -L -o main https://github.com/TheValkyrja/Anthropic2Vertex/releases/latest/download/main-${TARGETARCH} && \
    chmod 755 main

FROM gcr.io/distroless/cc-debian11

WORKDIR /app

# 从 builder 阶段复制下载的 main 文件
COPY --from=builder /main .

COPY model_mapping.json .
COPY .env .
COPY auth/auth.json auth/

# 复制 libz.so.1
COPY --from=builder /lib/*/libz.so.1 /lib/

ENV DOCKER_ENV=true
ENV LD_LIBRARY_PATH=/lib

CMD ["./main"]