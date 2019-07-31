.PHONY: all check clean

upgrade_flag = #-U

objects = $(wildcard *.in)
outputs := $(objects:.in=.txt)

all: $(outputs)


# Permit "unsafe" dependencies only for local development/testing
local.txt: local.in
	pip-compile --allow-unsafe -v $(upgrade_flag) --output-file $@ $<
test.txt: test.in
	pip-compile --allow-unsafe -v $(upgrade_flag) --output-file $@ $<


%.txt: %.in
	pip-compile -v $(upgrade_flag) --output-file $@ $<

test.txt: base.txt
dev.txt: base.txt
local.txt: test.txt
production.txt: base.txt

check:
	@which pip-compile > /dev/null

clean: check
	- rm *.txt
