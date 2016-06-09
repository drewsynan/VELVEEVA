IMAGENAME = drewsynan/velveeva
DOCKERFILE = .

.PHONY : install
install :
	python3 install

.PHONY : docker
docker :
	docker build -t $(IMAGENAME) $(DOCKERFILE)