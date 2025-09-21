all:
	curl -fLO "https://github.com/binzhang-u5f6c/multi-stream-lab-frontend/releases/download/v0.1.2/dist.tar.gz"
	tar -xzvf dist.tar.gz
	mv dist multistreamlab/dist
