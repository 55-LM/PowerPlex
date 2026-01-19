FROM node:18-alpine

WORKDIR /app
COPY package.json /app/package.json
RUN npm install

COPY . /app
ENV NODE_ENV=production

CMD ["npm", "run", "dev"]
