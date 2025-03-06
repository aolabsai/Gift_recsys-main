# Gift recommender system

Train multiple agents and come back to them




## Docker build instructions
The images can be built for both the backend and frontend with docker compose

There are some secrets that need to be stored when building and running the services. The keys are stored in a .env file that is not included in this repository. If you look at compose.yml you'll see that it is stored at the root of this repository.

**.env** needs to contain the following
```dotenv
OPENAI_KEY="key_here"

SER_API_KEY="key_here"

RAPID_KEY="key_here"

FIREBASE_SDK=json_here

AOLABS_API_KEY="key_here"

firebase_apikey="key_here"

GOOGLE_CLIENT_ID="key_here"

GOOGLE_CLIENT_SECRET="key_here"

VITE_BACKEND_URL="url_here"

FRONTEND_URL="url_here"
```

### Building the images
Once the .env files have the needed keys, you can build with one of the following commands
```
docker compose build
```
or
```
docker compose build --no-cache
```

#### optional alternatives
Or if you want to specify the url the backend will be at when building without editing the compose.yml file, you can use the following command
```
docker-compose build --build-arg VITE_BACKEND_URL="url_here"
```
or when building the images separately, you can use the following commands
```
#frontend
docker build --build-arg VITE_BACKEND_URL="url_here" .
#backend
docker build ./Backend
```

### Running the images
You can run both images with the following command, at least when you build the images with compose
```
docker compose up
```



### Tagging and pushing images to dockerhub
To push them to dockerhub tag and push them with the following commands
```
docker tag gift_recsys-main-backend  aolabs/giftrec-backend
docker push aolabs/giftrec-backend:latest
docker tag gift_recsys-main-frontend aolabs/giftrec-frontend
docker push aolabs/giftrec-frontend:latest
```
