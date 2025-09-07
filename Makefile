all: build
build: ; dub build --compiler=ldc2 --build=release
run: build ; ./primal_overlay
clean: ; dub clean && rm -f results.csv
