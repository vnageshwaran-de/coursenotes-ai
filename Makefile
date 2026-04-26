install:
	pip3 install -r requirements.txt
	python3 -m playwright install firefox

setup:
	python3 setup_session.py

run:
	python3 main.py
