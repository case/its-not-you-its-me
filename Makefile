.PHONY: install install-force uninstall test

SKILL_DIR := ~/.claude/skills/status-page

define do_install
	mkdir -p $(SKILL_DIR)
	cp -r skills/status-page/. $(SKILL_DIR)/
endef

install:
	@if [ -d $(SKILL_DIR) ]; then \
		echo "Error: $(SKILL_DIR) already exists"; \
		echo "Run 'make install-force' to overwrite"; \
		exit 1; \
	fi
	$(do_install)

install-force:
	$(do_install)

uninstall:
	rm -rf $(SKILL_DIR)

test:
	python3 -m unittest discover -s test -v
