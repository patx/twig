PREFIX ?= /usr/local
BINDIR ?= $(PREFIX)/bin
DATADIR ?= $(PREFIX)/share
APPDIR ?= $(DATADIR)/applications
ICONDIR ?= $(DATADIR)/icons/hicolor

.PHONY: install uninstall check

install:
	install -Dm755 twig.py "$(DESTDIR)$(BINDIR)/twig"
	install -Dm644 twig.desktop "$(DESTDIR)$(APPDIR)/twig.desktop"
	for size in 16 24 32 48 64 128 256 512; do \
		install -Dm644 "icons/hicolor/$${size}x$${size}/apps/twig.png" \
			"$(DESTDIR)$(ICONDIR)/$${size}x$${size}/apps/twig.png"; \
	done

uninstall:
	rm -f "$(DESTDIR)$(BINDIR)/twig"
	rm -f "$(DESTDIR)$(APPDIR)/twig.desktop"
	for size in 16 24 32 48 64 128 256 512; do \
		rm -f "$(DESTDIR)$(ICONDIR)/$${size}x$${size}/apps/twig.png"; \
	done

check:
	python3 -m py_compile twig.py
	python3 -m unittest discover -s tests
	desktop-file-validate twig.desktop
