BASEIMAGENAME = drewsynan/velveeva_base
BASEDOCKERFILE = dockerfiles/velveeva_base
CLIIMAGENAME = drewsynan/velveeva
CLIDOCKERFILE = dockerfiles/velveeva_cli

.PHONY : install
install :
	./install

.PHONY : docker_base
docker_base :
	docker build -t $(BASEIMAGENAME) $(BASEDOCKERFILE)

.PHONY : docker
docker :
	docker build -t $(CLIIMAGENAME) $(CLIDOCKERFILE)
