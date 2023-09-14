# Сборка backend образа 
cd ../backend
docker buildx build --platform=linux/amd64 -t luppiters/foodgram_backend . --push 
cd -

# Сборка frontend образа 
cd ../frontend 
docker buildx build --platform=linux/amd64 -t luppiters/foodgram_frontend . --push 
cd -
