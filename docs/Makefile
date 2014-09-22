# Makefile

MAN = clara.1 clara-images.1 clara-nodes.1 clara-p2p.1 clara-repo.1 clara-slurm.1

all: $(MAN)

clean:
	rm -f man/*.1 *.ps *.pdf *.html

# pandoc -s -t man pandoc.1.md -o example10.1

%.1:source/%.md; pandoc -s -t man $< -o man/$@

%.txt:%; ./$< -h 2>&1 > $@
%.html:man/%.1; rman -f HTML $< > $@
%.ps:man/%.1; groff -man $< > $@
%.pdf:%.ps; ps2pdf $< > $@
