.PHONY: install test

install:
	cp -r skills/status-page ~/.claude/skills/

test:
	python3 -m unittest discover -s test -v
