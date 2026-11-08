import argparse
import asyncio
import os
import re
from collections import deque
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
        RuntimeError: Если FaceFusion завершился с ошибкой или превысил допустимое время
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
        stderr=asyncio.subprocess.STDOUT,
    )

    try:
        output_tail = await asyncio.wait_for(read_output(process.stdout), timeout=FACEFUSION_TIMEOUT)
    except TimeoutError:
        process.kill()
        raise RuntimeError(f"FaceFusion не уложился в {FACEFUSION_TIMEOUT // 60} минут") from None
    except asyncio.CancelledError:
        process.kill()
        raise
    finally:
        await process.wait()

    if process.returncode != 0:
        raise RuntimeError(f"FaceFusion завершился с кодом {process.returncode}: {output_tail}")


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


async def read_output(stream: asyncio.StreamReader) -> str:
    """Выводит данные потока и возвращает последние 20 строк"""
    buffer = ""
    last_progress = None
    tail = deque(maxlen=20)
    while True:
        chunk = await stream.read(1024)
        if not chunk:
            break
        buffer += chunk.decode(errors="replace")
        parts = re.split(r"[\r\n]", buffer)
        buffer = parts.pop()

        for part in parts:
            part_data = parse_progress(part)
            if part_data:
                if last_progress != part_data:
                    print(part_data[0], part_data[1])
                    last_progress = part_data
            elif part:
                tail.append(part)
                print(part)
    if buffer:
        part_data = parse_progress(buffer)
        if part_data:
            print(part_data[0], part_data[1])
        else:
            tail.append(buffer)
            print(buffer)

    return "\n".join(tail)


def parse_progress(line: str) -> tuple[str, int] | None:
    """Парсит строку из потока facefusion и возвращает название процесса и %выполнения"""
    match = re.search(r"(\w+):\s+(\d+)%", line)
    if match:
        return match.group(1), int(match.group(2))
    return None


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