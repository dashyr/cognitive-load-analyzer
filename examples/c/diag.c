int squared(int x) {
    return x * x;
}

int diag(int x, int y, int z) {
    return squared(x) + squared(y) + squared(z);
}

int main(void) {
    return diag(3, 4, 5);
}
