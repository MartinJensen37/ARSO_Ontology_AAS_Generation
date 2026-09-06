# Dev-oriented frontend image: runs Vite's own dev server (not a static
# build) so hot-reload keeps working through the container. In
# docker-compose.yml the source tree is bind-mounted over this with
# node_modules shielded by an anonymous volume (see the compose file) so the
# Linux-native install done here at build time survives the mount.
FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev"]
