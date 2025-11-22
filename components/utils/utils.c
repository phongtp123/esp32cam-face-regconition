#include "stdio.h"
#include "stdlib.h"
#include "utils.h"

void intToString(int num, char *buffer, size_t size) {
    snprintf(buffer, size, "%d", num);
}
