# Use an official Node.js runtime as a parent image
FROM node:23

# Set the working directory in the container
WORKDIR /app

# Copy the package.json and package-lock.json files to the working directory
COPY package*.json ./

# Install the project dependencies
RUN npm install
COPY . ./
RUN npm run build

RUN npm install serve -g
# Copy the rest of the project files to the working directory
# COPY . .

# Build the Svelte project
# RUN npm run build

# FROM nginx:1.27-alpine

# COPY ./nginx.conf /etc/nginx/conf.d/default.conf
# COPY --from=build /app/dist /var/wwww/html/

# Expose the port the app runs on
EXPOSE 5173

# # Command to run the app
CMD ["serve", "-s", "dist", "-l", "5173"]