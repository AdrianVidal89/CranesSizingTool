FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Builds the static bundle and copies it to the shared volume nginx serves
# from. Runs once per `docker compose up`; there is no long-running server
# in this container.
CMD ["sh", "-c", "npm run build && mkdir -p /shared && cp -r dist/. /shared/"]
