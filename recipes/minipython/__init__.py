from pythonforandroid.recipe import Recipe
from pythonforandroid.util import current_directory, ensure_dir
from os.path import join, dirname
import os
import shlex
import subprocess
from shutil import copyfile

class MiniPythonRecipe(Recipe):
    name = 'minipython'
    version = '1.0'
    src_filename = 'mini_python.c'
    depends = ['python3']
    built_libraries = {
        'mini_python': 'mini_python'  # ELF binary we embed in APK
    }

    def get_recipe_env(self, arch):
        env = super().get_recipe_env(arch)

        python_recipe = self.get_recipe('python3', self.ctx)
        python_include = python_recipe.include_root(arch.arch)
        python_lib = python_recipe.link_root(arch.arch)

        libpython = join(python_lib, 'libpython3.11.a')  # adjust if needed
        env['CPPFLAGS'] = f'-I{python_include}'
        env['LDFLAGS'] = f'{libpython} -llog -landroid -ldl -lm'

        return env

    def get_source(self, arch):
        build_dir = self.get_build_dir(arch.arch)
        ensure_dir(build_dir)

        src = join(dirname(__file__), self.src_filename)
        dst = join(build_dir, self.src_filename)

        if not os.path.exists(dst):
            print(f"[minipython] Copying source from {src} to {dst}")
            copyfile(src, dst)

    def build_arch(self, arch):
        self.get_source(arch)
        build_dir = self.get_build_dir(arch.arch)
        env = self.get_recipe_env(arch)

        with current_directory(build_dir):
            cc = env.get('CC', 'clang')
            cfile = join(build_dir, self.src_filename)
            binfile = join(build_dir, 'mini_python')

            cmd = (
                f"{cc} -o {binfile} {cfile} "
                f"{env['CPPFLAGS']} {env['LDFLAGS']}"
            )

            print(f"[minipython] Compiling with: {cmd}")
            subprocess.check_call(shlex.split(cmd))

            #final_bin = join(self.ctx.get_libs_dir(arch.arch), 'mini_python')
            #print(f"[minipython] Copying binary to: {final_bin}")
            #copyfile(binfile, final_bin)
            #libs_dir = join(self.ctx.get_libs_dir(arch.arch))
            #ensure_dir(libs_dir)
            #final_bin = join(libs_dir, 'mini_python')  # must start with "lib" and end with ".so"
            #print(f"[minipython] Installing shared object to APK libs: {final_bin}")
            #copyfile(binfile, final_bin)
            
            #libs_dir = join(self.ctx.get_libs_dir(arch.arch))
            #ensure_dir(libs_dir)

            #binfile = join(build_dir, 'mini_python')  # this is your compiled binary
            #os.chmod(binfile, 0o755)  # make it executable

            #final_bin = join(libs_dir, 'mini_python')  # place directly into lib/<arch>/mini_python
            #print(f"[minipython] Installing executable to APK libs: {final_bin}")
            #copyfile(binfile, final_bin)
            libs_dir = self.ctx.get_libs_dir(arch.arch)
            ensure_dir(libs_dir)
            final_bin = join(libs_dir, 'libmini_python.so')  # Use .so extension to force inclusion
            copyfile(binfile, final_bin)
            os.chmod(final_bin, 0o755)  # Optional, but reinforces permission
            
            # 🔥 Add this block to ensure encodings is included
            stdlib_dir = join(self.ctx.get_python_install_dir(arch.arch), 'lib', 'python3.11')
            encodings_src = join(stdlib_dir, 'encodings')

            if os.path.exists(encodings_src):
                target_lib_dir = join(self.ctx.get_site_packages_dir(arch.arch), 'encodings')
                print(f"[minipython] Copying encodings to: {target_lib_dir}")
                shutil.copytree(encodings_src, target_lib_dir, dirs_exist_ok=True)
            else:
                print("[minipython] WARNING: encodings/ not found in stdlib!")




# Register the recipe
recipe = MiniPythonRecipe()
