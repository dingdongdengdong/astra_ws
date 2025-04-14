#!/bin/bash

# enter dev shell in docker container

IMG=registry.gitlab.com/roxautomation/images/python-dev

docker pull $IMG

# mount current directory to /workspace in container and run bash, set workdir to /workspace
docker run -it --rm \
            --network=host \
            -v $(pwd):/workspace \
            -w /workspace $IMG \
             bash

