FROM node:alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY index.js ./
USER node
EXPOSE 3000
CMD ["node", "index.js"]