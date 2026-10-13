#ifndef YS_SMS_VIDEO_H
#define YS_SMS_VIDEO_H

#include "sms_vdp.h"
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

enum {
    YS_SMS_SCREEN_WIDTH = 256,
    YS_SMS_SCREEN_HEIGHT = 192,
    YS_SMS_RGB_BYTES = YS_SMS_SCREEN_WIDTH * YS_SMS_SCREEN_HEIGHT * 3
};

typedef struct {
    uint32_t sprite_overflow_lines;
    uint32_t sprite_collision_pixels;
} YsSmsFrameStats;

/* Stateless 256x192 SMS VDP mode-4 snapshot, RGB888 output.
   Uses the already-written VDP VRAM/CRAM/register contents. This function
   intentionally does not generate VBlank or mutate the VDP status register.
   Non-mode-4 and display-disabled states render a solid backdrop. */
bool ys_sms_video_render(const YsSmsVdp *vdp, uint8_t *rgb, size_t size,
                         YsSmsFrameStats *stats);

/* Write a portable binary PPM image (P6), with no external dependencies. */
bool ys_sms_video_write_ppm(FILE *stream, const uint8_t *rgb, size_t size);
#endif
