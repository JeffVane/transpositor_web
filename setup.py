from cx_Freeze import setup, Executable
import os

# Nome do arquivo principal da aplicação
main_script = "app.py"

# Arquivos e pastas que serão incluídos no build
include_files = [
    ("templates", "templates"),
    ("static", "static"),
    ("uploads", "uploads"),         # opcional
    ("version.txt", "version.txt")  # essencial para checar atualizações

]

# Configurações de build
build_exe_options = {
    "packages": [
        "flask",
        "librosa",
        "soundfile",
        "numpy",
        "numba",
        "os",
        "shutil",
        "requests",
        "json",
        "time",
        "webbrowser"
    ],
    "include_files": include_files
}

# Executável
executables = [
    Executable(
        script=main_script,
        base="Win32GUI",  # use "Win32GUI" se quiser sem terminal
        target_name="Transpositor.exe",
        icon="icone.ico"
    )
]

# Setup da aplicação
setup(
    name="Transpositor Musical",
    version="1.0.0",
    description="Aplicativo para transposição de tons musicais",
    options={"build_exe": build_exe_options},
    executables=executables
)
