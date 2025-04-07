FROM node:18
WORKDIR /app
COPY node.js heartbeat.js package.json .
RUN npm install
CMD ["node", "node.js"]
