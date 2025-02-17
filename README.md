# Gift recommender system

Train multiple agents and come back to them




## Docker build instructions
The images can be built for both the backend and frontend with docker compose

There are some secrets that need to be stored when building
**.env** needs to contain the following
```dotenv
OPENAI_KEY="key_here"

SER_API_KEY="key_here"

RAPID_KEY="key_here"

FIREBASE_SDK=json_here

AOLABS_API_KEY="key_here"

firebase_apikey="key_here"

GOOGLE_CLIENT_ID = "key_here"

GOOGLE_CLIENT_SECRET = "key_here"
```

Once the .env files have the needed keys, you can build with one of the following commands
```
docker compose build
```
or
```
docker compose build --no-cache
```
the images can be run together with 
```
docker compose up
```

To push them to dockerhub tag and push them do the following
```
docker tag gift_recsys-main-backend  aolabs/giftrec-backend
docker push aolabs/giftrec-backend:latest
docker tag gift_recsys-main-frontend aolabs/giftrec-frontend
docker push aolabs/giftrec-frontend:latest
```
