CC=g++ $(COMPILER_OPTIONS)
COMPILER_OPTIONS=-std=c++11 -g

TOP = ..
INCLUDE = $(TOP)/include
BIN = bin
SRC = $(TOP)/src_cpp


all: 

	$(CC) -I$(INCLUDE) -I$(INCLUDE)/af/include -fPIC -c -o $(BIN)/algorithm.o $(SRC)/algorithm.cpp
	$(CC) -I$(INCLUDE) -I$(INCLUDE)/af/include -fPIC -c -o $(BIN)/bridge.o $(SRC)/bridge.cpp
	$(CC) -I$(INCLUDE) -I$(INCLUDE)/af/include -fPIC -c -o $(BIN)/manager.o $(SRC)/manager.cpp
	$(CC) -I$(INCLUDE) -I$(INCLUDE)/af/include -fPIC -c -o $(BIN)/parameters.o $(SRC)/parameters.cpp
	$(CC) -I$(INCLUDE) -I$(INCLUDE)/af/include -fPIC -c -o $(BIN)/state.o $(SRC)/state.cpp
	$(CC) -I$(INCLUDE) -I$(INCLUDE)/af/include -fPIC -c -o $(BIN)/support.o $(SRC)/support.cpp
	$(CC) -I$(INCLUDE) -I$(INCLUDE)/af/include -fPIC -c -o $(BIN)/worker.o $(SRC)/worker.cpp

	$(CC) -shared -Wl,-soname,$(abspath ../lib/libcdi.so) -o $(abspath ../lib/libcdi.so) $(BIN)/algorithm.o $(BIN)/bridge.o $(BIN)/manager.o $(BIN)/parameters.o $(BIN)/state.o $(BIN)/support.o $(BIN)/worker.o -lc

#$(CC) -o maincdi $(SRC)/main.cpp -L../lib -lcdi -lafopencl -lconfig++ -I$(INCLUDE)


