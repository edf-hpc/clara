# Makefile

MAN = clara.1 clara-images.1 clara-ipmi.1 clara-p2p.1 clara-repo.1 clara-slurm.1 clara-enc.1 clara-build.1 clara-virt.1 clara-chroot.1

all: $(MAN)
	pandoc --variable=geometry:a4paper users_guide.md -o users_guide.pdf

clean:
	rm -f man/*.1 *.ps *.pdf *.html

# pandoc -s -t man pandoc.1.md -o example10.1

%.1:source/%.md; pandoc -s -t man $< -o man/$@

%.txt:%; ./$< -h 2>&1 > $@
%.html:man/%.1; rman -f HTML $< > $@
%.ps:man/%.1; groff -man $< > $@
%.pdf:%.ps; ps2pdf $< > $@
