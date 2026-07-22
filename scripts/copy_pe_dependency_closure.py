from __future__ import annotations

import argparse
import json
import shutil
import struct
from pathlib import Path


def pe_imports(path: Path) -> list[str]:
    data = path.read_bytes()
    if len(data) < 64 or data[:2] != b"MZ":
        return []
    pe_offset = struct.unpack_from("<I", data, 0x3C)[0]
    if data[pe_offset : pe_offset + 4] != b"PE\0\0":
        return []
    coff_offset = pe_offset + 4
    section_count = struct.unpack_from("<H", data, coff_offset + 2)[0]
    optional_size = struct.unpack_from("<H", data, coff_offset + 16)[0]
    optional_offset = coff_offset + 20
    magic = struct.unpack_from("<H", data, optional_offset)[0]
    data_directory_offset = optional_offset + (112 if magic == 0x20B else 96)
    section_offset = optional_offset + optional_size
    sections = []
    for index in range(section_count):
        offset = section_offset + index * 40
        virtual_size = struct.unpack_from("<I", data, offset + 8)[0]
        virtual_address, raw_size, raw_pointer = struct.unpack_from(
            "<III",
            data,
            offset + 12,
        )
        sections.append(
            (
                virtual_address,
                max(virtual_size, raw_size),
                raw_pointer,
            )
        )

    def rva_to_offset(rva: int) -> int | None:
        for virtual_address, size, raw_pointer in sections:
            if virtual_address <= rva < virtual_address + size:
                return raw_pointer + rva - virtual_address
        return None

    imported_names = []
    for directory_index, descriptor_size, name_index in (
        (1, 20, 3),
        (13, 32, 1),
    ):
        rva, _ = struct.unpack_from(
            "<II",
            data,
            data_directory_offset + directory_index * 8,
        )
        if not rva:
            continue
        descriptor_offset = rva_to_offset(rva)
        if descriptor_offset is None:
            continue
        while descriptor_offset + descriptor_size <= len(data):
            values = struct.unpack_from(
                "<" + "I" * (descriptor_size // 4),
                data,
                descriptor_offset,
            )
            if not any(values):
                break
            name_offset = rva_to_offset(values[name_index])
            if name_offset is not None:
                end = data.find(b"\0", name_offset)
                if end >= 0:
                    imported_names.append(
                        data[name_offset:end].decode("ascii", "ignore")
                    )
            descriptor_offset += descriptor_size
    return imported_names


def copy_dependency_closure(
    seed: Path,
    source_directories: list[Path],
    target_root: Path,
) -> dict:
    local_files = {
        candidate.name.lower(): candidate
        for directory in source_directories
        for candidate in directory.glob("*.dll")
    }
    source_labels = {
        directory.resolve(): directory.name
        for directory in source_directories
    }
    queue = [seed]
    inspected = set()
    dependencies: dict[str, Path] = {}
    while queue:
        current = queue.pop()
        current_key = str(current.resolve()).lower()
        if current_key in inspected:
            continue
        inspected.add(current_key)
        for imported_name in pe_imports(current):
            dependency = local_files.get(imported_name.lower())
            if dependency is None:
                continue
            dependency_key = str(dependency.resolve()).lower()
            if dependency_key not in dependencies:
                dependencies[dependency_key] = dependency
                queue.append(dependency)

    copied = []
    total_bytes = 0
    for dependency in sorted(dependencies.values(), key=lambda item: item.name.lower()):
        source_parent = dependency.parent.resolve()
        label = source_labels[source_parent]
        target_directory = target_root / label
        target_directory.mkdir(parents=True, exist_ok=True)
        target = target_directory / dependency.name
        shutil.copy2(dependency, target)
        total_bytes += dependency.stat().st_size
        copied.append(
            {
                "source_group": label,
                "name": dependency.name,
                "bytes": dependency.stat().st_size,
            }
        )
    return {
        "seed": str(seed),
        "dependency_count": len(copied),
        "total_bytes": total_bytes,
        "files": copied,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Copy the local PE DLL dependency closure for a binary module."
    )
    parser.add_argument("--seed", required=True)
    parser.add_argument("--source-dir", action="append", required=True)
    parser.add_argument("--target-root", required=True)
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()

    result = copy_dependency_closure(
        Path(args.seed),
        [Path(value) for value in args.source_dir],
        Path(args.target_root),
    )
    manifest = Path(args.manifest)
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(
        "dependency closure: {} files, {:.1f} MB".format(
            result["dependency_count"],
            result["total_bytes"] / 1024 / 1024,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
