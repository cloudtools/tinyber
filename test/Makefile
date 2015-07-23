
CFLAGS = -g -O3

test: handwritten.c ../tinyber/data/tinyber.c ../tinyber/data/tinyber.h
	$(CC) $(CFLAGS) -I ../tinyber/data/ handwritten.c ../tinyber/data/tinyber.c -o handwritten
	./handwritten
