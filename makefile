BASEIMAGENAME = drewsynan/velveeva_base
BASEDOCKERFILE = velveeva_base
CLIIMAGENAME = drewsynan/velveeva
CLIDOCKERFILE = .

.PHONY : install
install :
	python3 install

.PHONY : docker_base
docker_base :
	docker build -t $(BASEIMAGENAME) $(BASEDOCKERFILE)

.PHONY : docker
docker :
	docker build -t $(CLIIMAGENAME) $(CLIDOCKERFILE)