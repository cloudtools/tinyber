
CFLAGS = -g -O3

test: test.c ../tinyber/data/tinyber.c ../tinyber/data/tinyber.h
	$(CC) $(CFLAGS) -I ../tinyber/data/ test.c ../tinyber/data/tinyber.c -o test
	./test
