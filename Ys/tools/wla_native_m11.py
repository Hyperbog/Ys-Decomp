#!/usr/bin/env python3
"""Build native Linux WLA-DX from the public repository or source archive.

By default clone the pinned public v10.7 release; use an optional local source
archive when network access is disabled. The Windows binary ZIPs are rejected.
Never conflate successful compilation with verified assembled game bytes.
Builds and external files stay outside the decompilation repository.
"""
import argparse
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tarfile
import tempfile
from zipfile import ZipFile

PUBLIC_REPO = "https://github.com/vhelin/wla-dx.git"
PINNED_REF = "v10.7"


def archive_type(path):
    if not path.is_file():
        raise FileNotFoundError(path)
    if path.suffix.lower() == '.zip':
        with ZipFile(path) as z:
            names = z.namelist()
            if any(PurePosixPath(n).name.lower() in ('wla-z80.exe', 'wlalink.exe')
                   for n in names) and not any(PurePosixPath(n).name == 'CMakeLists.txt'
                                               for n in names):
                raise ValueError('This is a Windows PE binary distribution. '
                                 'Upload the WLA-DX SOURCE ZIP (GitHub Code > Download ZIP).')
            if not any(PurePosixPath(n).name == 'CMakeLists.txt' for n in names):
                raise ValueError('Archive does not contain WLA-DX CMakeLists.txt source')
        return 'zip'
    if path.name.endswith(('.tar.gz', '.tgz')):
        with tarfile.open(path, 'r:gz') as tar:
            if not any(PurePosixPath(n.name).name == 'CMakeLists.txt'
                       for n in tar.getmembers() if n.isfile()):
                raise ValueError('Archive does not contain WLA-DX CMakeLists.txt source')
        return 'tar'
    raise ValueError('Expected a WLA-DX source .zip or .tar.gz archive')


def safe_archive_extract(path, destination):
    kind = archive_type(path)
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    if kind == 'zip':
        with ZipFile(path) as z:
            members = z.infolist()
            for item in members:
                p = PurePosixPath(item.filename)
                if p.is_absolute() or '..' in p.parts or item.file_size > 15_000_000:
                    raise ValueError('Unsafe or oversized source archive member')
                # Disallow Unix symlinks in untrusted source archives.
                if ((item.external_attr >> 16) & 0o170000) == 0o120000:
                    raise ValueError('Symlink inside source archive is not allowed')
            if sum(x.file_size for x in members) > 150_000_000:
                raise ValueError('WLA source archive is unreasonably large')
            z.extractall(destination)
    else:
        with tarfile.open(path, 'r:gz') as tar:
            members = tar.getmembers()
            for item in members:
                p = PurePosixPath(item.name)
                if p.is_absolute() or '..' in p.parts or not (item.isfile() or item.isdir()) or item.size > 15_000_000:
                    raise ValueError('Unsafe or oversized source archive member')
            if sum(x.size for x in members) > 150_000_000:
                raise ValueError('WLA source archive is unreasonably large')
            for item in members:
                tar.extract(item, destination, filter='data')
    cmake = list(destination.rglob('CMakeLists.txt'))
    if not cmake:
        raise ValueError('No CMakeLists.txt in extracted WLA-DX source')
    roots = [c.parent for c in cmake if (c.parent/'README.md').is_file() or (c.parent/'README').is_file()]
    if len(roots) != 1:
        raise ValueError('Could not uniquely identify WLA-DX source root')
    return roots[0]


def clone_public_source(workdir):
    """Clone the pinned public upstream release; fail closed if network is blocked."""
    root = Path(workdir).resolve() / 'wla-dx-v10.7-public'
    if (root / 'CMakeLists.txt').is_file() and (root / 'README.md').is_file():
        return root
    if root.exists():
        raise ValueError(f'Incomplete WLA-DX source checkout: {root}')
    if not shutil.which('git'):
        raise FileNotFoundError('Git is required to fetch public WLA-DX source')
    try:
        subprocess.run(['git', '-c', 'credential.interactive=never', 'clone',
                        '--depth', '1', '--branch', PINNED_REF, PUBLIC_REPO, str(root)],
                       check=True, timeout=120, capture_output=True, text=True,
                       env={**os.environ, 'GIT_TERMINAL_PROMPT': '0'})
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        shutil.rmtree(root, ignore_errors=True)
        detail = getattr(exc, 'stderr', '') or str(exc)
        raise RuntimeError(
            f'Cannot download public WLA-DX {PINNED_REF}: {detail.strip()}. '
            'This container may lack DNS/network egress. '
            'Provide the source archive as the optional positional argument.'
        ) from exc
    if not (root / 'CMakeLists.txt').is_file():
        raise ValueError('Public WLA-DX checkout lacks CMakeLists.txt')
    return root


def build_native(source, workdir, *, verify=True):
    for tool in ('cmake', 'cc'):
        if not shutil.which(tool):
            raise FileNotFoundError(f'Missing native build prerequisite: {tool}')
    workdir = Path(workdir).resolve()
    workdir.mkdir(parents=True, exist_ok=True)
    source_root = (safe_archive_extract(Path(source), workdir/'source')
                   if source is not None else clone_public_source(workdir))
    build = workdir/'build'
    subprocess.run(['cmake', '-S', str(source_root), '-B', str(build),
                    '-DCMAKE_BUILD_TYPE=Release'], check=True, timeout=180)
    subprocess.run(['cmake', '--build', str(build), '--parallel', '4'],
                   check=True, timeout=300)
    candidates = [*build.rglob('wla-z80'), *source_root.rglob('wla-z80')]
    linkers = [*build.rglob('wlalink'), *source_root.rglob('wlalink')]
    assemblers = [p for p in candidates if p.is_file() and p.stat().st_mode & 0o111]
    linkers = [p for p in linkers if p.is_file() and p.stat().st_mode & 0o111]
    if not assemblers or not linkers:
        raise RuntimeError('CMake returned successfully but no native wla-z80/wlalink found')
    assembler, linker = assemblers[0], linkers[0]
    result = {'assembler_path': str(assembler), 'linker_path': str(linker),
              'external_assembler_verified': False}
    if verify:
        from wla_system_m10 import verify as verify_ys
        result.update(verify_ys(workdir/'verification', str(assembler), str(linker)))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source_archive', nargs='?', type=Path,
                        help='Optional WLA-DX source ZIP; otherwise fetch public v10.7 Git tag')
    parser.add_argument('--workdir', type=Path, help='Persistent build directory outside Git')
    parser.add_argument('--build-only', action='store_true',
                        help='Skip Ys independent matching (not a verification result)')
    args = parser.parse_args()
    if not args.workdir:
        with tempfile.TemporaryDirectory(prefix='ys_wla_native_m11_') as td:
            print(build_native(args.source_archive, td, verify=not args.build_only))
    else:
        print(build_native(args.source_archive, args.workdir, verify=not args.build_only))


if __name__ == '__main__':
    main()
