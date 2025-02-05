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

# Copy the rest of the project files to the working directory
# COPY . .

# Build the Svelte project
# RUN npm run build


# Expose the port the app runs on
EXPOSE 5173

# # Command to run the app
CMD ["npm", "run", "dev"]