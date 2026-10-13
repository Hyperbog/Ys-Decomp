/* Windows-only, zero-SDL, zero-ROM graphical HARDWARE DIAGNOSTIC.
   It is not a playable Ys game.  Do not rename it ys-native-game. */
#define WIN32_LEAN_AND_MEAN
#define UNICODE
#define _UNICODE
#include <windows.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>
#include "sms_video.h"
#include "video_fixture.h"
#include "sms_clock.h"

enum { FRAME_TIMER = 1, WINDOW_SCALE = 3, INFO_HEIGHT = 96 };

typedef struct {
    YsSmsVdp vdp;
    YsSmsClock clock;
    uint8_t rgb[YS_SMS_RGB_BYTES];
    uint8_t bgra[YS_SMS_SCREEN_WIDTH * YS_SMS_SCREEN_HEIGHT * 4];
    BITMAPINFO bitmap;
    unsigned frame;
    int sprite_x;
    int sprite_y;
    BOOL paused;
    BOOL ready;
} Diagnostic;

static Diagnostic state;

static BOOL update_frame(Diagnostic *app) {
    YsSmsFrameStats stats;
    if (!ys_sms_clock_advance(&app->clock, &app->vdp,
                               ys_sms_clock_tstates_per_frame(&app->clock)))
        return FALSE;
    /* Test fixture: scrolling graphics. Movement is from host arrow keys.
       These pixels and controls ARE NOT Ys title art or game logic. */
    ys_sms_video_fixture_animate(&app->vdp, app->frame++);
    app->vdp.vram[0x3F80u] = (uint8_t)app->sprite_x;
    app->vdp.vram[0x3F00u] = (uint8_t)(app->sprite_y - 1);
    if (!ys_sms_video_render(&app->vdp, app->rgb,
                             sizeof(app->rgb), &stats))
        return FALSE;
    for (size_t i = 0; i < sizeof(app->rgb) / 3; ++i) {
        app->bgra[4 * i + 0] = app->rgb[3 * i + 2];
        app->bgra[4 * i + 1] = app->rgb[3 * i + 1];
        app->bgra[4 * i + 2] = app->rgb[3 * i + 0];
        app->bgra[4 * i + 3] = 255u;
    }
    /* Native clock event consumed by our synthetic fixture driver.
       The real game ISR is not connected to this window. */
    uint8_t status = 0;
    if (!ys_sms_vdp_read(&app->vdp, 0xBFu, &status) ||
        (status & 0x80u) == 0)
        return FALSE;
    return TRUE;
}

static int self_test(void) {
    YsSmsVdp *vdp = malloc(sizeof(*vdp));
    uint8_t *rgb = malloc(YS_SMS_RGB_BYTES);
    YsSmsClock clock;
    int success = 0;
    if (vdp && rgb && ys_sms_clock_reset(&clock, YS_SMS_NTSC)) {
        ys_sms_video_fixture_init(vdp);
        if (ys_sms_clock_advance(&clock, vdp,
                                ys_sms_clock_tstates_per_frame(&clock)) &&
            ys_sms_video_render(vdp, rgb, YS_SMS_RGB_BYTES, NULL) &&
            clock.frames == 1 && clock.vblank_events == 1 &&
            (vdp->status & 0x80u) != 0)
            success = 1;
    }
    free(vdp);
    free(rgb);
    return success ? 0 : 1;
}

static void paint(HWND hwnd, HDC dc) {
    RECT client;
    GetClientRect(hwnd, &client);
    int width = client.right - client.left;
    int height = client.bottom - client.top;
    int image_height = height - INFO_HEIGHT;
    if (width < 1 || image_height < 1)
        return;
    HBRUSH backing = CreateSolidBrush(RGB(18, 22, 31));
    if (backing) {
        FillRect(dc, &client, backing);
        DeleteObject(backing);
    }
    SetStretchBltMode(dc, COLORONCOLOR);
    if (state.ready)
        StretchDIBits(dc, 0, 0, width, image_height,
                      0, 0, YS_SMS_SCREEN_WIDTH, YS_SMS_SCREEN_HEIGHT,
                      state.bgra, &state.bitmap, DIB_RGB_COLORS, SRCCOPY);
    SetBkMode(dc, TRANSPARENT);
    SetTextColor(dc, RGB(235, 241, 255));
    RECT title = {12, image_height + 5, width - 10, image_height + 33};
    DrawTextW(dc, L"DEVELOPMENT VIDEO TEST - NOT YS GAMEPLAY",
              -1, &title, DT_LEFT | DT_SINGLELINE | DT_VCENTER);
    SetTextColor(dc, RGB(186, 196, 213));
    RECT keys = {12, image_height + 33, width - 10, image_height + 59};
    DrawTextW(dc, L"Arrow keys: move test sprite    Space: pause/resume    F1: help    Esc: exit",
              -1, &keys, DT_LEFT | DT_SINGLELINE | DT_VCENTER);
    wchar_t status[200];
    swprintf(status, sizeof(status) / sizeof(status[0]),
             L"NTSC frame %u  |  VBlank events %llu  |  Sprite x=%d y=%d  |  %ls",
             state.frame, (unsigned long long)state.clock.vblank_events,
             state.sprite_x, state.sprite_y, state.paused ? L"Paused" : L"Running");
    RECT foot = {12, image_height + 60, width - 10, height - 4};
    DrawTextW(dc, status, -1, &foot, DT_LEFT | DT_SINGLELINE | DT_VCENTER);
}

static LRESULT CALLBACK window_proc(HWND hwnd, UINT msg,
                                    WPARAM wp, LPARAM lp) {
    (void)lp;
    switch (msg) {
    case WM_CREATE:
        ys_sms_video_fixture_init(&state.vdp);
        if (!ys_sms_clock_reset(&state.clock, YS_SMS_NTSC)) return -1;
        state.sprite_x = 120;
        state.sprite_y = 63;
        memset(&state.bitmap, 0, sizeof(state.bitmap));
        state.bitmap.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
        state.bitmap.bmiHeader.biWidth = YS_SMS_SCREEN_WIDTH;
        state.bitmap.bmiHeader.biHeight = -YS_SMS_SCREEN_HEIGHT; /* top-down */
        state.bitmap.bmiHeader.biPlanes = 1;
        state.bitmap.bmiHeader.biBitCount = 32;
        state.bitmap.bmiHeader.biCompression = BI_RGB;
        state.ready = update_frame(&state);
        if (!state.ready || !SetTimer(hwnd, FRAME_TIMER, 16, NULL))
            return -1;
        return 0;
    case WM_TIMER:
        if (wp == FRAME_TIMER && !state.paused) {
            if (!update_frame(&state)) {
                KillTimer(hwnd, FRAME_TIMER);
                MessageBoxW(hwnd, L"Internal SMS video diagnostic failed.",
                            L"Ys Development", MB_OK | MB_ICONERROR);
                DestroyWindow(hwnd);
                return 0;
            }
            InvalidateRect(hwnd, NULL, FALSE);
        }
        return 0;
    case WM_KEYDOWN:
        switch (wp) {
        case VK_ESCAPE: DestroyWindow(hwnd); return 0;
        case VK_SPACE: state.paused = !state.paused; break;
        case VK_LEFT: state.sprite_x -= 4; break;
        case VK_RIGHT: state.sprite_x += 4; break;
        case VK_UP: state.sprite_y -= 4; break;
        case VK_DOWN: state.sprite_y += 4; break;
        case VK_F1:
            MessageBoxW(hwnd,
                L"This is a standalone Windows GDI test of the SMS renderer.\n"
                L"No ROM is required and no Ys gameplay code runs.\n\n"
                L"Use START_HERE.cmd to test the cartridge CPU diagnostics.\n"
                L"Those tools require your own valid Ys SMS ROM.\n"
                L"This diagnostic does not yet qualify as Alpha.",
                L"About this Development build", MB_OK | MB_ICONINFORMATION);
            break;
        default: return DefWindowProcW(hwnd, msg, wp, lp);
        }
        if (state.sprite_x < 0) state.sprite_x = 0;
        if (state.sprite_x > 248) state.sprite_x = 248;
        if (state.sprite_y < 0) state.sprite_y = 0;
        if (state.sprite_y > 192) state.sprite_y = 192;
        /* Show keyboard motion immediately, even while paused. */
        state.vdp.vram[0x3F80] = (uint8_t)state.sprite_x;
        state.vdp.vram[0x3F00] = (uint8_t)(state.sprite_y-1);
        if (state.ready) {
            YsSmsFrameStats stats;
            state.ready = ys_sms_video_render(&state.vdp, state.rgb,
                                               sizeof(state.rgb), &stats);
            if (state.ready) {
                for (size_t i = 0; i < sizeof(state.rgb) / 3; ++i) {
                    state.bgra[i * 4] = state.rgb[i * 3 + 2];
                    state.bgra[i * 4 + 1] = state.rgb[i * 3 + 1];
                    state.bgra[i * 4 + 2] = state.rgb[i * 3];
                    state.bgra[i * 4 + 3] = 255;
                }
            }
        }
        InvalidateRect(hwnd, NULL, FALSE);
        return 0;
    case WM_PAINT: {
        PAINTSTRUCT ps;
        HDC dc = BeginPaint(hwnd, &ps);
        paint(hwnd, dc);
        EndPaint(hwnd, &ps);
        return 0;
    }
    case WM_DESTROY:
        KillTimer(hwnd, FRAME_TIMER);
        PostQuitMessage(0);
        return 0;
    default: return DefWindowProcW(hwnd, msg, wp, lp);
    }
}

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE previous,
                    PWSTR command_line, int show) {
    (void)previous;
    if (command_line && wcsstr(command_line, L"--self-test"))
        return self_test();
    WNDCLASSEXW cls;
    memset(&cls, 0, sizeof(cls));
    cls.cbSize = sizeof(cls);
    cls.hInstance = instance;
    cls.lpfnWndProc = window_proc;
    cls.lpszClassName = L"YsNativeSmsVideoDiagnostics";
    cls.hCursor = LoadCursorW(NULL, IDC_ARROW);
    cls.hIcon = LoadIconW(NULL, IDI_APPLICATION);
    cls.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1);
    if (!RegisterClassExW(&cls)) {
        MessageBoxW(NULL, L"Could not register the Windows diagnostic window.",
                    L"Ys Development", MB_OK | MB_ICONERROR);
        return 1;
    }
    RECT area = {0, 0, YS_SMS_SCREEN_WIDTH * WINDOW_SCALE,
                 YS_SMS_SCREEN_HEIGHT * WINDOW_SCALE + INFO_HEIGHT};
    AdjustWindowRect(&area, WS_OVERLAPPEDWINDOW, FALSE);
    HWND hwnd = CreateWindowExW(0, cls.lpszClassName,
        L"Ys Native SMS - M31 Development Hardware Preview (NOT GAMEPLAY)",
        WS_OVERLAPPEDWINDOW, CW_USEDEFAULT, CW_USEDEFAULT,
        area.right - area.left, area.bottom - area.top,
        NULL, NULL, instance, NULL);
    if (!hwnd) {
        MessageBoxW(NULL, L"Could not create the Windows diagnostic window.",
                    L"Ys Development", MB_OK | MB_ICONERROR);
        return 1;
    }
    ShowWindow(hwnd, show);
    UpdateWindow(hwnd);
    MSG msg;
    while (GetMessageW(&msg, NULL, 0, 0) > 0) {
        TranslateMessage(&msg);
        DispatchMessageW(&msg);
    }
    return (int)msg.wParam;
}
