#include <Python.h>
#include <stdio.h>

int main(int argc, char *argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: mini_python script.py\n");
        return 1;
    }

    wchar_t *program = Py_DecodeLocale(argv[0], NULL);
    Py_SetProgramName(program);
    Py_Initialize();

    FILE *fp = fopen(argv[1], "r");
    if (!fp) {
        fprintf(stderr, "Could not open %s\n", argv[1]);
        return 1;
    }

    //PySys_SetArgv(argc - 1, (wchar_t *[]) {Py_DecodeLocale(argv[1], NULL)});
    wchar_t **argv_w = (wchar_t **)malloc(sizeof(wchar_t *) * argc);
    for (int i = 0; i < argc; i++) {
        argv_w[i] = Py_DecodeLocale(argv[i], NULL);
        }
    PySys_SetArgv(argc, argv_w);

    PyRun_SimpleFile(fp, argv[1]);
    fclose(fp);
    Py_Finalize();
    PyMem_RawFree(program);
    return 0;
}

