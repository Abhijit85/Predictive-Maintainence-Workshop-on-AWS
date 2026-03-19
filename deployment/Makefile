IMAGE = predictive-one-click:latest

# Environment variables
# (AWS Configuration)
AWS_REGION=""
AWS_ACCESS_KEY_ID="" 
AWS_SECRET_ACCESS_KEY="" 
AWS_SESSION_TOKEN=""

# Docker Environment Variables
ENVS ?= AWS_ACCESS_KEY_ID=$(AWS_ACCESS_KEY_ID) AWS_SECRET_ACCESS_KEY=$(AWS_SECRET_ACCESS_KEY) AWS_SESSION_TOKEN=$(AWS_SESSION_TOKEN) AWS_REGION=$(AWS_REGION)


# Docker Volumes
STATIC_VOLUMES = ./states:/states ./input:/app_files ./output:/output
CREATE_ONLY_ECR = ./config/only-ecr.tfvars.json:/app/terraform/config/config.tfvars.json
DEPLOY_WITH_BUILD = ./config/deploy-with-build.tfvars.json:/app/terraform/config/config.tfvars.json
DEPLOY_WITH_PUBLIC_ECR = ./config/deploy-with-public-ecr.tfvars.json:/app/terraform/config/config.tfvars.json

VOLUMES ?=

# Convert to Docker flags
DOCKER_VOLUMES := $(foreach vol,$(STATIC_VOLUMES) $(VOLUMES),-v $(vol))
DOCKER_ENVS := $(foreach env,$(ENVS),-e $(env))

# App Flags
APP_FLAGS ?=

# -------------------------------------------------------------------
#                          Targets
# -------------------------------------------------------------------

# ==== Build One-Click Deployment image ====

build:
	cp -r ../ui one-click/ui
	docker build -f one-click/Dockerfile -t $(IMAGE) ./one-click/
	rm -rf one-click/ui


# ==== Build/Updates with private ECR ====

# Uses config for just creating ECR, in build case
create-private-ecr:
	docker run --rm -it $(DOCKER_VOLUMES) -v $(CREATE_ONLY_ECR) $(DOCKER_ENVS) $(IMAGE) one-click apply $(APP_FLAGS)

# Publish to private ECR repository, in build case
build-and-publish-private-ecr:
	bash ./scripts/build_and_publish.sh $(AWS_REGION) $(AWS_ACCESS_KEY_ID) $(AWS_SECRET_ACCESS_KEY) $(AWS_SESSION_TOKEN)

# Applies infrastructure, with build case
apply-with-build:
	docker run --rm -it $(DOCKER_VOLUMES) -v $(DEPLOY_WITH_BUILD) $(DOCKER_ENVS) $(IMAGE) one-click apply $(APP_FLAGS)

# Main Target
deploy-with-build:
	-$(MAKE) create-private-ecr
	$(MAKE) build-and-publish-private-ecr
	$(MAKE) apply-with-build


# ==== Destroys full infrastructure with private ECR  ====

destroy-with-build:
	docker run --rm -it $(DOCKER_VOLUMES) -v $(DEPLOY_WITH_BUILD) $(DOCKER_ENVS) $(IMAGE) one-click destroy $(APP_FLAGS)


# ==== Build/Updates with public ECR ====

deploy-with-public-ecr:
	docker run --rm -it $(DOCKER_VOLUMES) -v $(DEPLOY_WITH_PUBLIC_ECR) $(DOCKER_ENVS) $(IMAGE) one-click apply $(APP_FLAGS)


# ==== Destroys full infrastructure with public ECR ====

destroy-with-public-ecr:
	docker run --rm -it $(DOCKER_VOLUMES) -v $(DEPLOY_WITH_PUBLIC_ECR) $(DOCKER_ENVS) $(IMAGE) one-click destroy $(APP_FLAGS)


# ==== Removes One-Click Deployment image ====

clean:
	docker image rm $(IMAGE)