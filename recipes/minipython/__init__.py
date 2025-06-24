# mini_python_recipe

from pythonforandroid.recipe import Recipe
from pythonforandroid.util import current_directory, ensure_dir
from os.path import join, dirname, exists
import os
import shlex
import subprocess
import shutil
from shutil import copyfile

class MiniPythonRecipe(Recipe):
    name = 'minipython'
    version = '1.0'
    src_filename = 'mini_python.c'
    depends = ['python3']
    
    def get_recipe_env(self, arch):
        env = super().get_recipe_env(arch)

        python_recipe = self.get_recipe('python3', self.ctx)
        python_include = python_recipe.include_root(arch.arch)
        python_lib = python_recipe.link_root(arch.arch)
        python_src = python_recipe.get_build_dir(arch.arch)

        # Find the actual libpython name
        libpython_candidates = [
            join(python_lib, 'libpython3.11.a'),
            join(python_lib, 'libpython3.11.so'),
            join(python_lib, 'libpython3.so'),
        ]
        
        libpython = None
        for candidate in libpython_candidates:
            if exists(candidate):
                libpython = candidate
                break
        
        if not libpython:
            raise Exception("Could not find libpython")

        env['CPPFLAGS'] = f'-I{python_include} -I{python_src}/Include -I{python_src}/Modules -I{python_src}/Include/internal'
        env['LDFLAGS'] = f'{libpython} -llog -landroid -ldl -lm -lz'
        env['PYTHON_SRC'] = python_src

        return env

    def get_source(self, arch):
        build_dir = self.get_build_dir(arch.arch)
        ensure_dir(build_dir)

        src = join(dirname(__file__), self.src_filename)
        dst = join(build_dir, self.src_filename)

        if not exists(dst):
            print(f"[minipython] Copying source from {src} to {dst}")
            copyfile(src, dst)
            
        # Copy Python module source files for embedding
        env = self.get_recipe_env(arch)
        python_src = env['PYTHON_SRC']
        modules_dir = join(python_src, 'Modules')
        
        # Copy essential module sources
        essential_modules = [
            '_struct.c',
            'structmodule.c', 
            '_multiprocessing/multiprocessing.c',
            '_multiprocessing/semaphore.c',
            '_posixsubprocess.c',
            'selectmodule.c',
            'socketmodule.c',
            '_pickle.c',
            'fcntlmodule.c',
            'timemodule.c',
            'arraymodule.c',
            'mathmodule.c',
            '_randommodule.c'
        ]
        
        for module_file in essential_modules:
            src_path = join(modules_dir, module_file)
            if exists(src_path):
                # Create subdirectories if needed
                dst_file = join(build_dir, 'modules', module_file)
                ensure_dir(dirname(dst_file))
                copyfile(src_path, dst_file)
                print(f"[minipython] Copied {module_file}")

    def create_embedded_modules_c(self, arch):
        """Create a C file that includes all the module sources"""
        build_dir = self.get_build_dir(arch.arch)
        
        embedded_c_content = '''
// Embedded Python modules for multiprocessing support
#define PY_SSIZE_T_CLEAN
#include <Python.h>

// Include the actual Python module implementations
#ifdef HAVE_STRUCT_MODULE
#include "modules/_struct.c"
#elif defined(HAVE_STRUCTMODULE)
#include "modules/structmodule.c"
#endif

#ifdef HAVE_MULTIPROCESSING
#include "modules/_multiprocessing/multiprocessing.c"
#include "modules/_multiprocessing/semaphore.c"
#endif

#ifdef HAVE_POSIXSUBPROCESS
#include "modules/_posixsubprocess.c"
#endif

#ifdef HAVE_SELECT
#include "modules/selectmodule.c"
#endif

// Module initialization table
static struct _inittab embedded_modules[] = {
    {"_struct", PyInit__struct},
    {"_multiprocessing", PyInit__multiprocessing},
    {"_posixsubprocess", PyInit__posixsubprocess},
    {"select", PyInit_select},
    {NULL, NULL}
};

int init_embedded_modules(void) {
    return PyImport_ExtendInittab(embedded_modules);
}
'''
        
        with open(join(build_dir, 'embedded_modules.c'), 'w') as f:
            f.write(embedded_c_content)

    def build_arch(self, arch):
        self.get_source(arch)
        self.create_embedded_modules_c(arch)
        build_dir = self.get_build_dir(arch.arch)
        env = self.get_recipe_env(arch)

        with current_directory(build_dir):
            cc = env.get('CC', 'clang')
            cfile = join(build_dir, self.src_filename)
            embedded_file = join(build_dir, 'embedded_modules.c')
            binfile = join(build_dir, 'mini_python')

            # Check which modules we actually have
            defines = []
            modules_dir = join(build_dir, 'modules')
            if exists(join(modules_dir, '_struct.c')):
                defines.append('-DHAVE_STRUCT_MODULE')
            elif exists(join(modules_dir, 'structmodule.c')):
                defines.append('-DHAVE_STRUCTMODULE')
                
            if exists(join(modules_dir, '_multiprocessing')):
                defines.append('-DHAVE_MULTIPROCESSING')
            if exists(join(modules_dir, '_posixsubprocess.c')):
                defines.append('-DHAVE_POSIXSUBPROCESS')
            if exists(join(modules_dir, 'selectmodule.c')):
                defines.append('-DHAVE_SELECT')

            defines_str = ' '.join(defines)

            cmd = (
                f"{cc} -o {binfile} {cfile} {embedded_file} "
                f"{env['CPPFLAGS']} {env['LDFLAGS']} {defines_str} -static-libstdc++"
            )

            print(f"[minipython] Compiling with: {cmd}")
            subprocess.check_call(shlex.split(cmd))

            # Install the binary
            libs_dir = self.ctx.get_libs_dir(arch.arch)
            ensure_dir(libs_dir)
            
            final_bin = join(libs_dir, 'mini_python')
            copyfile(binfile, final_bin)
            os.chmod(final_bin, 0o755)
            print(f"[minipython] Installed executable to: {final_bin}")

            # Ensure Python standard library is available
            self._copy_python_stdlib(arch)

    def _copy_python_stdlib(self, arch):
        """Copy essential Python stdlib modules"""
        python_recipe = self.get_recipe('python3', self.ctx)
        stdlib_dir = join(python_recipe.get_build_dir(arch.arch), 'Lib')
        
        if not exists(stdlib_dir):
            print("[minipython] WARNING: Python stdlib not found!")
            return

        # Copy essential modules
        essential_modules = [
            'encodings',
            'collections',
            'os.py',
            'sys.py',
            'types.py',
            'io.py',
            'abc.py',
            'functools.py',
            'operator.py',
            'keyword.py',
            'heapq.py',
            'reprlib.py',
            'weakref.py'
        ]

        site_packages = self.ctx.get_site_packages_dir(arch.arch)
        ensure_dir(site_packages)

        for module in essential_modules:
            src_path = join(stdlib_dir, module)
            if exists(src_path):
                dst_path = join(site_packages, module)
                if os.path.isdir(src_path):
                    if exists(dst_path):
                        shutil.rmtree(dst_path)
                    shutil.copytree(src_path, dst_path)
                else:
                    copyfile(src_path, dst_path)
                print(f"[minipython] Copied {module} to site-packages")

# Register the recipe
recipe = MiniPythonRecipe()
