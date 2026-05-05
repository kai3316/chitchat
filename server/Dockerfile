# ---- Build stage -----------------------------------------------------------
FROM golang:1.22-alpine AS builder

RUN apk add --no-cache ca-certificates git

WORKDIR /src

COPY go.mod go.sum* ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 go build -ldflags="-s -w" -o /relay-server .

# ---- Run stage -------------------------------------------------------------
FROM alpine:3.19

RUN apk add --no-cache ca-certificates tzdata

# Create non-root user.
RUN addgroup -S relay && adduser -S relay -G relay

COPY --from=builder /relay-server /usr/local/bin/relay-server

USER relay
EXPOSE 8080

ENTRYPOINT ["/usr/local/bin/relay-server"]
