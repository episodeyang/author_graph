default:
	make install
install:
	pip install -r requirements.txt
start-jupyter:
	jupyter notebook --ip=* --port=5000

