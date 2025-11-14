#!/usr/bin/env python3
"""Тестовый скрипт для проверки разбиения аудио на чанки."""

import subprocess
import json
from pathlib import Path

def test_audio_split(audio_file: str):
    """Проверяет, как файл разбивается на чанки."""
    file_path = Path(audio_file)

    if not file_path.exists():
        print(f"Файл не найден: {audio_file}")
        return

    # Получаем длительность файла
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        str(file_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Ошибка ffprobe: {result.stderr}")
        return

    probe_data = json.loads(result.stdout)
    total_duration = float(probe_data.get("format", {}).get("duration", 0))

    print(f"Исходный файл: {audio_file}")
    print(f"Длительность: {total_duration:.2f} секунд ({total_duration/60:.2f} минут)")

    # Параметры разбиения
    chunk_duration = 50
    overlap = 1.0
    step = chunk_duration - overlap

    # Рассчитываем ожидаемое количество чанков
    expected_chunks = int((total_duration - overlap) / step) + 1

    print(f"\nПараметры разбиения:")
    print(f"  Длительность чанка: {chunk_duration} сек")
    print(f"  Overlap: {overlap} сек")
    print(f"  Step: {step} сек")
    print(f"\nОжидаемое количество чанков: {expected_chunks}")

    # Симулируем разбиение
    chunks = []
    start_time = 0.0
    chunk_index = 0

    while start_time < total_duration:
        chunk_index += 1
        actual_duration = min(chunk_duration, total_duration - start_time)
        chunks.append({
            'index': chunk_index,
            'start': start_time,
            'duration': actual_duration,
            'end': start_time + actual_duration
        })
        start_time += step
        if start_time >= total_duration:
            break

    print(f"Фактическое количество чанков: {len(chunks)}")
    print(f"\nПервые 5 чанков:")
    for chunk in chunks[:5]:
        print(f"  Чанк {chunk['index']:3d}: {chunk['start']:7.2f}s - {chunk['end']:7.2f}s (длительность: {chunk['duration']:.2f}s)")

    if len(chunks) > 5:
        print(f"  ...")
        print(f"\nПоследние 3 чанка:")
        for chunk in chunks[-3:]:
            print(f"  Чанк {chunk['index']:3d}: {chunk['start']:7.2f}s - {chunk['end']:7.2f}s (длительность: {chunk['duration']:.2f}s)")

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Использование: python test_audio_split.py <путь_к_аудио_файлу>")
        sys.exit(1)

    test_audio_split(sys.argv[1])
