#include <Python.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>

int main(int argc, char *argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: mini_python script.py [args...]\n");
        return 1;
    }

    const char *python_path = getenv("PYTHONPATH");
    if (!python_path) {

        setenv("PYTHONPATH", "/data/data/org.test.idekivy/files/lib/python3.11/site-packages", 1);
    }


    wchar_t *program = Py_DecodeLocale(argv[0], NULL);
    if (!program) {
        fprintf(stderr, "Fatal error: cannot decode argv[0]\n");
        return 1;
    }
    
    Py_SetProgramName(program);
    

    if (Py_Initialize() != 0) {
        fprintf(stderr, "Failed to initialize Python\n");
        return 1;
    }


    wchar_t **argv_w = (wchar_t **)malloc(sizeof(wchar_t *) * argc);
    if (!argv_w) {
        fprintf(stderr, "Memory allocation failed\n");
        Py_Finalize();
        return 1;
    }

    for (int i = 0; i < argc; i++) {
        argv_w[i] = Py_DecodeLocale(argv[i], NULL);
        if (!argv_w[i]) {
            fprintf(stderr, "Fatal error: cannot decode argv[%d]\n", i);

            for (int j = 0; j < i; j++) {
                PyMem_RawFree(argv_w[j]);
            }
            free(argv_w);
            PyMem_RawFree(program);
            Py_Finalize();
            return 1;
        }
    }
    
    PySys_SetArgv(argc, argv_w);

    FILE *fp = fopen(argv[1], "r");
    if (!fp) {
        fprintf(stderr, "Could not open %s\n", argv[1]);

        for (int i = 0; i < argc; i++) {
            PyMem_RawFree(argv_w[i]);
        }
        free(argv_w);
        PyMem_RawFree(program);
        Py_Finalize();
        return 1;
    }

    int result = PyRun_SimpleFile(fp, argv[1]);
    fclose(fp);

    for (int i = 0; i < argc; i++) {
        PyMem_RawFree(argv_w[i]);
    }
    free(argv_w);
    PyMem_RawFree(program);
    
    if (Py_FinalizeEx() < 0) {
        return 120;
    }
    
    return result;
}
