CFLAGS ?= -g
LDFLAGS = -lgsoap

OBJS = googleapi.o soapClient.o soapC.o

libgoogleapi.a: $(OBJS)
	ar rcs $@ $^

clean:
	rm -f libgoogleapi.a $(OBJS)
