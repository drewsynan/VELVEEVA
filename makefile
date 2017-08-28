BASEIMAGENAME = drewsynan/velveeva_base
BASEDOCKERFILE = dockerfiles/velveeva_base
BASEVERSION = legacy
CLIIMAGENAME = drewsynan/velveeva
CLIDOCKERFILE = dockerfiles/velveeva_cli
CLIVERSION = legacy

.PHONY : install
install :
	./install

.PHONY : docker_base
docker_base :
	docker build -t $(BASEIMAGENAME):$(BASEVERSION) $(BASEDOCKERFILE)

.PHONY : docker
docker :
	docker build -t $(CLIIMAGENAME):$(CLIVERSION) $(CLIDOCKERFILE)
