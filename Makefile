install:
	pip install -r requirements.txt
	playwright install firefox

setup:
	python3 setup_session.py

run:
	python3 main.py
