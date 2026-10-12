import os
from pathlib import Path
import logging


# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s]: %(message)s:'
)

project_name = "transcriber"
list_of_files = [

    ".github/workflows/.gitkeep",


    f"src/{project_name}/__init__.py",
    f"src/{project_name}/api/__init__.py",
    f"src/{project_name}/api/routes.py",
    f"src/{project_name}/config/__init__.py",
    f"src/{project_name}/config/settings.py",
    f"src/{project_name}/services/__init__.py",
    f"src/{project_name}/services/transcription.py",
    f"src/{project_name}/services/audio.py",
    f"src/{project_name}/services/deduplication.py",
    f"src/{project_name}/services/governance.py",
    f"src/{project_name}/services/guardrails.py",
    f"src/{project_name}/models/__init__.py",
    f"src/{project_name}/models/response.py",
    f"src/{project_name}/constants/__init__.py",
    f"src/{project_name}/constants/audio.py",
    f"src/{project_name}/utils/__init__.py",
    f"src/{project_name}/utils/logging.py",
    "tests/__init__.py",
    "tests/test_transcription.py",
    ".env",
    ".gitignore",
    "requirements.txt",
    "app.py",
    "README.md",
    "research/transcription_test.ipynb",
]

for filepath in list_of_files:

    filepath = Path(filepath)

    filedir, filename = os.path.split(filepath)

    if filedir != "":
        os.makedirs(filedir, exist_ok=True)

        logging.info(
            f"Creating directory: {filedir} for file: {filename}"
        )

    if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:

        with open(filepath, "w") as f:
            pass

        logging.info(
            f"Creating empty file: {filepath}"
        )

    else:
        logging.info(
            f"{filename} already exists"
        )