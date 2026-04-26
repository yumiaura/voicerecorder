FROM node:20-alpine

WORKDIR /opt/www

COPY package.json package-lock.json* ./

CMD ["sh", "-c", "npm install && node server.js"]
