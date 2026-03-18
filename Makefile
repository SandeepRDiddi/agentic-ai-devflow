.PHONY: setup dev test lint fmt benchmark eval docker-up docker-down

setup:
	pip install hatch && hatch env create

dev:
	hatch run dev

test:
	hatch run test

lint:
	hatch run lint

fmt:
	hatch run fmt

benchmark:
	hatch run benchmark

eval:
	hatch run eval

docker-up:
	docker compose up --build

docker-down:
	docker compose down
