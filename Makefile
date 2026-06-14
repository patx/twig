PREFIX ?= /usr/local
BINDIR ?= $(PREFIX)/bin
DATADIR ?= $(PREFIX)/share
APPDIR ?= $(DATADIR)/applications
ICONDIR ?= $(DATADIR)/icons/hicolor
MANDIR ?= $(DATADIR)/man
PACKAGE ?= twig
VERSION ?= 0.1.0
DEB_ARCH ?= all
DEB_BUILD_DIR ?= build/deb
DEB_ROOT ?= $(DEB_BUILD_DIR)/$(PACKAGE)
DEB_FILE ?= dist/$(PACKAGE)_$(VERSION)_$(DEB_ARCH).deb
DEB_CHANGELOG_DATE ?= $(shell date -R)

.PHONY: install uninstall check deb clean-deb

install:
	install -Dm755 twig.py "$(DESTDIR)$(BINDIR)/twig"
	install -Dm644 twig.desktop "$(DESTDIR)$(APPDIR)/twig.desktop"
	install -Dm644 docs/twig.1 "$(DESTDIR)$(MANDIR)/man1/twig.1"
	for size in 16 24 32 48 64 128 256 512; do \
		install -Dm644 "icons/hicolor/$${size}x$${size}/apps/twig.png" \
			"$(DESTDIR)$(ICONDIR)/$${size}x$${size}/apps/twig.png"; \
	done

uninstall:
	rm -f "$(DESTDIR)$(BINDIR)/twig"
	rm -f "$(DESTDIR)$(APPDIR)/twig.desktop"
	rm -f "$(DESTDIR)$(MANDIR)/man1/twig.1"
	for size in 16 24 32 48 64 128 256 512; do \
		rm -f "$(DESTDIR)$(ICONDIR)/$${size}x$${size}/apps/twig.png"; \
	done

check:
	python3 -m py_compile twig.py
	python3 -m unittest discover -s tests
	desktop-file-validate twig.desktop

deb: check clean-deb
	$(MAKE) install DESTDIR="$(CURDIR)/$(DEB_ROOT)" PREFIX=/usr
	install -Dm644 LICENSE "$(DEB_ROOT)/usr/share/doc/$(PACKAGE)/copyright"
	install -Dm644 README.md "$(DEB_ROOT)/usr/share/doc/$(PACKAGE)/README.md"
	install -d "$(DEB_ROOT)/usr/share/doc/$(PACKAGE)"
	printf '%s\n\n%s\n\n%s\n' "$(PACKAGE) ($(VERSION)) stable; urgency=medium" "  * Build local Debian package." " -- harrison erd <me@harrisonerd.com>  $(DEB_CHANGELOG_DATE)" | gzip -9n > "$(DEB_ROOT)/usr/share/doc/$(PACKAGE)/changelog.gz"
	chmod 0644 "$(DEB_ROOT)/usr/share/doc/$(PACKAGE)/changelog.gz"
	gzip -9n "$(DEB_ROOT)/usr/share/man/man1/twig.1"
	install -d "$(DEB_ROOT)/DEBIAN"
	printf '%s\n' \
		"Package: $(PACKAGE)" \
		"Version: $(VERSION)" \
		"Section: editors" \
		"Priority: optional" \
		"Architecture: $(DEB_ARCH)" \
		"Maintainer: Harrison Erd <me@harrisonerd.com>" \
		"Depends: python3, python3-gi, gir1.2-gtk-3.0, gir1.2-gtksource-4 | gir1.2-gtksource-3.0" \
		"Description: Lightweight GTK code editor" \
		" Twig is a small GTK code editor for lightweight Linux desktops." \
		" It supports one file per window, syntax highlighting, line numbers," \
		" find and replace, undo and redo, and save-before-close prompts." \
		> "$(DEB_ROOT)/DEBIAN/control"
	install -d dist
	dpkg-deb --build --root-owner-group "$(DEB_ROOT)" "$(DEB_FILE)"

clean-deb:
	rm -rf "$(DEB_BUILD_DIR)" dist/*.deb
