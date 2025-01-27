# Stage 1: Build stage
FROM alpine:latest AS builder

# Install build dependencies and Python runtime
RUN apk update && apk add --no-cache python3 py3-pip py3-pillow

# Set the working directory
WORKDIR /opt

# Copy the current directory contents into /opt in the builder container
COPY . /opt/

# Install the Python package in the builder
RUN pip3 install --break-system-packages .

# Stage 2: Final runtime stage
FROM alpine:latest

# Install only runtime dependencies
RUN apk add --no-cache python3 py3-flask

# Copy the application from the builder stage
COPY --from=builder /opt /opt

# Set the working directory
WORKDIR /opt

# Set the entrypoint
ENTRYPOINT ["python3", "-m", "ycast"]
