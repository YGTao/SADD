typedef long long llong;
int test2char64(char *p) {}
int test1char8(char c) {}
int test1short32(short c) {}
int test2short32(short *p) {}
typedef llong vllong1 __attribute__((__vector_size__(sizeof(llong))));
vllong1 test2llong1(llong *p) {
    llong c = *test1char8;
    vllong1 v = {c};
    return v;
}
int main() {}