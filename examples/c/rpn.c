#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

int eval_rpn(const char *expr) {
    int stack[64];
    int sp = 0;
    char *copy = strdup(expr);
    char *tok = strtok(copy, " ");
    while (tok) {
        if (isdigit((unsigned char)tok[0]) || (tok[0]=='-' && isdigit((unsigned char)tok[1]))) {
            stack[sp++] = atoi(tok);
        } else {
            int b = stack[--sp];
            int a = stack[--sp];
            if (tok[0] == '+') stack[sp++] = a + b;
            else if (tok[0] == '-') stack[sp++] = a - b;
            else if (tok[0] == '*') stack[sp++] = a * b;
            else if (tok[0] == '/') stack[sp++] = a / b;
        }
        tok = strtok(NULL, " ");
    }
    int res = stack[--sp];
    free(copy);
    return res;
}
