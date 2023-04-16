FROM node:18.8.0-alpine3.16
WORKDIR /app
RUN apk update && apk upgrade && \
    apk add --no-cache bash git openssh
RUN yarn add react-scripts@5.0.1 -g --silent

ADD frontend /app
COPY ./docker/react/react.sh /scripts/react.sh
RUN chmod +x /scripts/react.sh
