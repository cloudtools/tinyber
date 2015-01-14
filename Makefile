
test: test.c tinyber.c tinyber.h
	$(CC) $(CFLAGS) test.c -o test tinyber.c
