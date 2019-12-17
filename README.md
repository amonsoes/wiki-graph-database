HOW TO RUN THE APP

in routes.py, change the amount of desired results. default is 5 results per request.

- build the image with:

docker build -t wikidumps .

- run the image with:

docker run -p 5000:5000 -v $PWD:/code wikidumps


