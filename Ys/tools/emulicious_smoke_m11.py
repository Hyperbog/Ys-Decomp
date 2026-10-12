#!/usr/bin/env python3
"""Independent Emulicious boot/render smoke test for the ROM-free Ys build.

Requires external Emulicious.jar, Java/JDK, Xvfb, xwininfo, Pillow.
Compiles the screen-capture helper at run time. No emulator executable, ROM or
image payload is included in the source repository. This proves a bounded GUI
boot/render observation, NOT whole-game equivalence or independent assembly.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time

from build_system_m10 import build

# Logo region excludes blinking title text (at y~70) and credits (at y~250).
TITLE_ROI = (40, 90, 260, 250)
# SHA-256 of RGB pixel bytes, from an independently booted Emulicious session.
TITLE_SHA256 = 'fea1432fc67f05d2ac2d63f2865392597964794978643f743726c73f5b40f39d'
ROM_SHA256 = '02e9404e81bddd4ca21fef2b2711dfe562c3bd7b230bf042df3142362e29a6a9'

HELPER_JAVA = r'''
import java.awt.*;
import java.awt.event.InputEvent;
import java.awt.image.BufferedImage;
import javax.imageio.ImageIO;
import java.io.File;
public class ScreenCaptureM11 {
    public static void main(String[] args) throws Exception {
        Robot robot = new Robot();
        if (args.length == 1 && args[0].equals("dismiss-update-dialog")) {
            int[][] points = {{20, 194}, {175, 238}};
            for (int[] xy : points) {
                robot.mouseMove(xy[0], xy[1]);
                robot.mousePress(InputEvent.BUTTON1_DOWN_MASK);
                robot.delay(100);
                robot.mouseRelease(InputEvent.BUTTON1_DOWN_MASK);
                robot.delay(300);
            }
            return;
        }
        BufferedImage image = robot.createScreenCapture(
            new Rectangle(Toolkit.getDefaultToolkit().getScreenSize()));
        ImageIO.write(image, "png", new File(args[0]));
    }
}
'''


def digest(data):
    return hashlib.sha256(data).hexdigest()


def title_observation(png):
    from PIL import Image
    with Image.open(png) as image:
        image = image.convert('RGB')
        if image.size[0] < TITLE_ROI[2] or image.size[1] < TITLE_ROI[3]:
            raise ValueError('Emulator capture dimensions too small')
        crop = image.crop(TITLE_ROI)
        colors = len(crop.getcolors(100000) or [])
        return {'logo_rgb_sha256': digest(crop.tobytes()), 'unique_colors': colors,
                'roi': list(TITLE_ROI)}


def check_tools(jar):
    if not jar.is_file():
        raise FileNotFoundError('Emulicious.jar is required (--jar)')
    for tool in ('java', 'javac', 'Xvfb', 'xwininfo'):
        if not shutil.which(tool):
            raise FileNotFoundError(f'Missing external runtime prerequisite: {tool}')
    try:
        from PIL import Image  # noqa: F401
    except ImportError as exc:
        raise RuntimeError('Install Pillow to inspect emulator screenshots') from exc


def compile_helper(folder):
    source = folder / 'ScreenCaptureM11.java'
    source.write_text(HELPER_JAVA)
    subprocess.run(['javac', str(source)], check=True, capture_output=True,
                   text=True, timeout=20)


def find_dialog(display_env):
    tree = subprocess.run(['xwininfo', '-root', '-tree'], env=display_env,
                          check=True, capture_output=True, text=True, timeout=8).stdout
    match = re.search(r'(0x[0-9a-fA-F]+) "Emulicious - Update Behaviour"', tree)
    if not match:
        return False
    details = subprocess.run(['xwininfo', '-id', match.group(1)], env=display_env,
                             check=True, capture_output=True, text=True, timeout=8).stdout
    return 'Map State: IsViewable' in details


def boot_and_capture(rom, jar, folder, *, deadline_seconds=40):
    # -displayfd reserves an available display without racing other Xvfb jobs.
    rfd, wfd = os.pipe()
    xvfb = None
    emulator = None
    try:
        xvfb = subprocess.Popen(['Xvfb', '-displayfd', str(wfd), '-screen', '0',
                                '800x600x24', '-nolisten', 'tcp'],
                                pass_fds=(wfd,), stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
        os.close(wfd)
        wfd = -1
        display = os.read(rfd, 64).strip().decode('ascii')
        if not display.isdigit():
            raise RuntimeError('Virtual display failed to initialize')
        env = os.environ.copy()
        env['DISPLAY'] = ':' + display
        env['JAVA_TOOL_OPTIONS'] = '-Djava.awt.headless=false'
        command = ['java', '-jar', str(jar), '-muted', '-scale', '2', str(rom)]
        emulator = subprocess.Popen(command, env=env, stdout=subprocess.DEVNULL,
                                    stderr=subprocess.PIPE)
        dialog_dismissed = False
        until = time.monotonic() + deadline_seconds
        png = folder / ('capture_' + rom.stem.replace(' ', '_') + '.png')
        last = None
        while time.monotonic() < until:
            if emulator.poll() is not None:
                detail = emulator.stderr.read().decode(errors='replace')[-2000:]
                raise RuntimeError('Emulicious exited before rendering: ' + detail)
            if not dialog_dismissed and find_dialog(env):
                subprocess.run(['java', '-cp', str(folder), 'ScreenCaptureM11',
                                'dismiss-update-dialog'], env=env, check=True,
                               stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=8)
                dialog_dismissed = True
                time.sleep(.8)
            subprocess.run(['java', '-cp', str(folder), 'ScreenCaptureM11', str(png)],
                           env=env, check=True, stdout=subprocess.DEVNULL,
                           stderr=subprocess.PIPE, timeout=8)
            last = title_observation(png)
            # Compare an actual rendered image, not merely whether Java started.
            if last['logo_rgb_sha256'] == TITLE_SHA256 and last['unique_colors'] >= 8:
                return last
            time.sleep(1.2)
        raise AssertionError('Emulicious did not reach the expected Ys title-art image'
                             f' in {deadline_seconds}s; last observation={last}')
    finally:
        os.close(rfd)
        if wfd != -1:
            os.close(wfd)
        for process in (emulator, xvfb):
            if process is not None and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=4)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=4)


def run(jar, reference=None, *, deadline_seconds=40):
    check_tools(jar)
    image, _ = build()
    if digest(image) != ROM_SHA256:
        raise ValueError('Source-built ROM fingerprint mismatch')
    if reference is not None and digest(reference.read_bytes()) != ROM_SHA256:
        raise ValueError('Reference ROM fingerprint mismatch')
    with tempfile.TemporaryDirectory(prefix='ys_emulicious_m11_') as temp:
        folder = Path(temp)
        compile_helper(folder)
        generated = folder / 'Ys-source-rebuilt.sms'
        generated.write_bytes(image)
        source_observation = boot_and_capture(generated, jar, folder,
                                            deadline_seconds=deadline_seconds)
        baseline_observation = None
        if reference:
            baseline_observation = boot_and_capture(reference, jar, folder,
                                                    deadline_seconds=deadline_seconds)
            if baseline_observation['logo_rgb_sha256'] != source_observation['logo_rgb_sha256']:
                raise AssertionError('Original and source-built emulator output differs')
    return {'schema': 'ys-emulicious-independent-boot-m11-v1',
            'emulator': 'Emulicious', 'jar_sha256': digest(jar.read_bytes()),
            'rebuilt_rom_sha256': digest(image), 'rebuilt_rom_bytes': len(image),
            'source_only_build': True, 'original_rom_booted': reference is not None,
            'title_observation': source_observation,
            'reference_title_observation': baseline_observation,
            'boot_and_title_render_passed': True,
            'emulated_gameplay_verified': False,
            'emulated_audio_verified': False,
            'external_assembler_verified': False,
            'note': 'GUI title-art pixel check, not full-game behavioral equivalence.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jar', required=True, type=Path,
                        help='Owner-supplied Emulicious.jar, kept outside Git')
    parser.add_argument('--reference-rom', type=Path,
                        help='Optional owned original ROM for second emulator boot')
    parser.add_argument('--report', type=Path,
                        help='Output JSON report without screenshots or ROM')
    parser.add_argument('--deadline', type=int, default=40)
    args = parser.parse_args()
    if args.deadline < 5 or args.deadline > 180:
        parser.error('Deadline must be between 5 and 180 seconds')
    result = run(args.jar, args.reference_rom, deadline_seconds=args.deadline)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
