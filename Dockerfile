FROM debian:11-slim AS builder

RUN apt-get update && apt-get install -y \
    zlib1g \
    && rm -rf /var/lib/apt/lists/*

FROM gcr.io/distroless/cc-debian11

WORKDIR /app

COPY --from=builder /lib/x86_64-linux-gnu/libz.so.1 /lib/x86_64-linux-gnu/libz.so.1

COPY --chmod=755 main .
COPY model_mapping.json .
COPY .env .
COPY auth/auth.json auth/

ENV DOCKER_ENV=true

CMD ["./main"]