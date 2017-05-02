REGISTRY='datagridsys'
IMAGE='skopos-plugin-swarm-exec'
TAG?='latest'
IMAGESPEC=$(REGISTRY)/$(IMAGE):$(TAG)

.PHONY: all container push

all: container

container:
	docker build -t $(IMAGESPEC) .

push: container
	docker push $(IMAGESPEC)