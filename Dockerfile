# Use an official Node.js runtime as a parent image
FROM node:23 AS build_image


# reference on build args/environment variables in docker + vite
# https://stackoverflow.com/questions/77486735/docker-with-vite-env-variables-are-undefined-inside-the-docker-container/77490465#77490465
ARG VITE_BACKEND_URL


# Set the working directory in the container
WORKDIR /app

# Copy the package.json and package-lock.json files to the working directory
COPY package*.json ./

# Install the project dependencies
#TODO: npm ci?
# - https://docs.npmjs.com/cli/v6/commands/npm-ci
RUN npm install

# Copy the rest of the project files to the working directory
COPY . ./
# Build the Svelte project
RUN npm run build

#TODO: add to package.json?
RUN npm install serve -g


# TODO: multi-stage build 

# FROM nginx:1.27-alpine

# COPY ./nginx.conf /etc/nginx/conf.d/default.conf
# COPY --from=build /app/dist /var/wwww/html/

# FROM nginx:1.27-alpine as PRODUCTION_IMAGE
# COPY ./nginx.conf /etc/nginx/conf.d/default.conf
# COPY --from=BUILD_IMAGE /app/dist /var/wwww/html/


# Expose the port the app runs on
# TODO: port change?
EXPOSE 5173

# # Command to run the app
# # -s specifies what to serve, -l is where to listen
CMD ["serve", "-s", "dist", "-l", "5173"]
# CMD ["nginx", "-g", "daemon off;"]