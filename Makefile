BAKE_OPTIONS=--no-input

help:
	@echo "bake 	Generate project using defaults"
	@echo "help 	Show this help"
	@echo "test 	Run the tests"
	@echo "replay 	Replay last cookiecutter run and watch for changes"
	@echo "watch 	Generate project using defaults and watch for changes"
	

bake:  # Generate project using defaults
	cookiecutter --config-file test_config.json $(BAKE_OPTIONS) . --overwrite-if-exists

watch: bake
	watchmedo shell-command -p '*.*' -c 'make bake -e BAKE_OPTIONS=$(BAKE_OPTIONS)' -W -R -D \{{cookiecutter.project_name}}/

replay: BAKE_OPTIONS=--replay
replay: watch
	;

test:
	pytest
