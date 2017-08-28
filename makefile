BASEIMAGENAME = drewsynan/velveeva_base
BASEDOCKERFILE = dockerfiles/velveeva_base
BASEVERSION = 1.1.0
CLIIMAGENAME = drewsynan/velveeva
CLIDOCKERFILE = dockerfiles/velveeva_cli
CLIVERSION = 1.2.0

.PHONY : install
install :
	./install

.PHONY : docker_base
docker_base :
	docker build -t $(BASEIMAGENAME):$(BASEVERSION) $(BASEDOCKERFILE)

.PHONY : docker
docker :
	docker build -t $(CLIIMAGENAME):$(CLIVERSION) $(CLIDOCKERFILE)
