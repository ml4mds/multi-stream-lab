all: pip.complete multistreamlab/dist
	touch all.complete

sync.temp:
	python3 -m pip install multistreamlab
	touch pip.complete

multistreamlab/dist:
	curl -fLO "https://github.com/binzhang-u5f6c/multi-stream-lab-frontend/releases/download/v0.1.2/dist.tar.gz"
	tar -xzvf dist.tar.gz
	mv dist multistreamlab/dist

clean:
	rm dist.tar.gz
	rm -rf multistreamlab/dist
	rm pip.complete
	rm all.complete
