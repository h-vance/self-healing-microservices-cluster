FROM python:3.12-alpine

# kubectl is the only runtime dependency; the controller itself is stdlib-only.
ARG KUBECTL_VERSION=v1.31.0
RUN apk add --no-cache curl \
    && curl -fsSLo /usr/local/bin/kubectl \
       "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl" \
    && chmod +x /usr/local/bin/kubectl \
    && apk del curl \
    && addgroup -S app && adduser -S -G app app

WORKDIR /app
COPY controller.py /app/controller.py

ENV PORT=8080 \
    EVIDENCE_DIR=/tmp/evidence

EXPOSE 8080
USER app
CMD ["python", "/app/controller.py"]
