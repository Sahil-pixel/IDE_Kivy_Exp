#include <Python.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>

// External function to initialize embedded modules
extern int init_embedded_modules(void);

// Fallback minimal implementations if embedded modules aren't available
#ifndef HAVE_STRUCT_MODULE
#ifndef HAVE_STRUCTMODULE
// Minimal _struct module implementation
static PyMethodDef struct_methods[] = {
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef struct_module = {
    PyModuleDef_HEAD_INIT,
    "_struct",
    "Provides conversion between Python values and C structs",
    -1,
    struct_methods,
    NULL, NULL, NULL, NULL
};

PyMODINIT_FUNC PyInit__struct(void) {
    PyObject *m;
    m = PyModule_Create(&struct_module);
    if (m == NULL)
        return NULL;
    
    if (PyModule_AddStringConstant(m, "__version__", "1.0") < 0) {
        Py_DECREF(m);
        return NULL;
    }
    
    return m;
}
#endif
#endif

#ifndef HAVE_MULTIPROCESSING
// Minimal multiprocessing module
static PyMethodDef multiprocessing_methods[] = {
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef multiprocessing_module = {
    PyModuleDef_HEAD_INIT,
    "_multiprocessing",
    "Low-level multiprocessing support",
    -1,
    multiprocessing_methods,
    NULL, NULL, NULL, NULL
};

PyMODINIT_FUNC PyInit__multiprocessing(void) {
    return PyModule_Create(&multiprocessing_module);
}
#endif

// Fallback built-in modules table
static struct _inittab fallback_modules[] = {
#ifndef HAVE_STRUCT_MODULE
#ifndef HAVE_STRUCTMODULE
    {"_struct", PyInit__struct},
#endif
#endif
#ifndef HAVE_MULTIPROCESSING
    {"_multiprocessing", PyInit__multiprocessing},
#endif
    {NULL, NULL}
};

int main(int argc, char *argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: mini_python script.py [args...]\n");
        return 1;
    }

    // Try to register embedded modules first
    if (init_embedded_modules() < 0) {
        // If embedded modules fail, use fallback implementations
        fprintf(stderr, "Warning: Using fallback module implementations\n");
        if (PyImport_ExtendInittab(fallback_modules) < 0) {
            fprintf(stderr, "Failed to extend built-in modules table\n");
            return 1;
        }
    }

    // Set up Python path to find modules
    const char *python_path = getenv("PYTHONPATH");
    if (!python_path) {
        // Set a default path for Android
        setenv("PYTHONPATH", "/data/data/org.test.idekivy/files/lib/python3.11/site-packages", 1);
    }

    // Initialize Python
    wchar_t *program = Py_DecodeLocale(argv[0], NULL);
    if (!program) {
        fprintf(stderr, "Fatal error: cannot decode argv[0]\n");
        return 1;
    }
    
    Py_SetProgramName(program);
    
    // Initialize Python interpreter
    if (Py_Initialize() != 0) {
        fprintf(stderr, "Failed to initialize Python\n");
        return 1;
    }

    // Set up sys.argv
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
            // Clean up allocated memory
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

    // Run the Python script
    FILE *fp = fopen(argv[1], "r");
    if (!fp) {
        fprintf(stderr, "Could not open %s\n", argv[1]);
        // Clean up
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

    // Clean up
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
