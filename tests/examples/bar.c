#include <stdio.h>

int main(int argc, char *argv[]) {
    if (argc < 1) {
        puts("missing required argument");
        return 1;
    }

    printf("got: %s\n", argv[1]);
    return 0;
}
