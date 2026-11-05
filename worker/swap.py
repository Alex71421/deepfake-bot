import argparse
import asyncio
import os
from pathlib import Path

FACEFUSION_DIRECTORY = Path(r"D:\PythonProjects\facefusion")
FACEFUSION_PYTHON = Path(r"C:\Users\user\miniconda3\envs\facefusion\python.exe")
OUTPUT_DIR = Path(r"D:\PythonProjects\deepfake-bot\data\output")
INPUT_DIR = Path(r"D:\PythonProjects\deepfake-bot\data\input")
FACEFUSION_ENV_DIR = FACEFUSION_PYTHON.parent
FACEFUSION_TIMEOUT = 30 * 60


async def run_facefusion(source: Path, target: Path, output: Path, face_selector_mode: str = "many") -> None:
    """Заменяет лицо в видео с помощью FaceFusion.

    Args:
        source: путь к фото с лицом для замены
        target: путь к обрабатываемому видео
        output: путь куда будет сохранен результат
        face_selector_mode: режим сколько лиц будет заменено на видео

    Raises:
        FileNotFoundError: Если source или target не существуют
        RuntimeError: Если FaceFusion завершился с ошибкой
    """
    if not source.is_file():
        raise FileNotFoundError(f"файл не найден: {source}")
    if not target.is_file():
        raise FileNotFoundError(f"файл не найден: {target}")

    output.parent.mkdir(parents=True, exist_ok=True)

    command = [
        str(FACEFUSION_PYTHON),
        str(FACEFUSION_DIRECTORY / "facefusion.py"),
        "headless-run",
        "-s", str(source),
        "-t", str(target),
        "-o", str(output),
        "--processors", "face_swapper", "face_enhancer",
        "--face-detector-score", "0.7",
        "--execution-providers", "cuda",
        "--face-selector-mode", face_selector_mode,
        "--reference-face-distance", "0.5",
        "--output-video-quality", "70",
        "--output-audio-encoder", "aac",
    ]

    process = await asyncio.create_subprocess_exec(
        *command,
        cwd=FACEFUSION_DIRECTORY,
        env=build_facefusion_env(),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        raise RuntimeError(f"FaceFusion завершился с кодом {process.returncode}: "
                           f"{stderr.decode(errors='replace') or stdout.decode(errors='replace')}")


def get_output_name(folder: Path) -> Path:
    """Возвращает свободное имя файла в формате result_x.mp4"""
    file_number = 1
    while True:
        candidate = folder / f"result_{file_number}.mp4"
        if not candidate.exists():
            return candidate
        file_number += 1


def build_facefusion_env() -> dict[str, str]:
    """Возвращает копию окружения с путями FaceFusion"""
    env = os.environ.copy()
    facefusion_paths = os.pathsep.join([
        str(FACEFUSION_ENV_DIR),
        str(FACEFUSION_ENV_DIR / "Library" / "bin"),
        str(FACEFUSION_ENV_DIR / "Scripts"),
    ])

    env["PATH"] = facefusion_paths + os.pathsep + env["PATH"]
    return env


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=["many", "one", "reference"],
        default="many",
        help="режим сколько лиц будет заменено на видео",
    )
    args = parser.parse_args()

    output_path = get_output_name(OUTPUT_DIR)
    asyncio.run(run_facefusion(INPUT_DIR / "photo.jpg", INPUT_DIR / "video.mp4", output_path, face_selector_mode=args.mode))
    print(f"Результат сохранен в {OUTPUT_DIR} под именем {output_path.name}")