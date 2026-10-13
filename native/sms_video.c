#include "sms_video.h"
#include <string.h>

static uint16_t wrap_vram(unsigned address) {
    return (uint16_t)(address & (YS_VRAM_BYTES - 1u));
}

static void color_rgb(const YsSmsVdp *vdp, unsigned index, uint8_t *pixel) {
    uint8_t cram = vdp->cram[index & 31u];
    pixel[0] = (uint8_t)((cram & 3u) * 85u);
    pixel[1] = (uint8_t)(((cram >> 2) & 3u) * 85u);
    pixel[2] = (uint8_t)(((cram >> 4) & 3u) * 85u);
}

static unsigned tile_pixel(const YsSmsVdp *vdp, unsigned tile,
                           unsigned x, unsigned y, unsigned pattern_base) {
    unsigned base = (pattern_base + tile * 32u + y * 4u) & 0x3FFFu;
    unsigned shift = 7u - x;
    unsigned value = 0u;
    for (unsigned plane = 0; plane != 4u; ++plane)
        value |= ((unsigned)(vdp->vram[wrap_vram(base + plane)] >> shift) & 1u)
                 << plane;
    return value;
}

bool ys_sms_video_render(const YsSmsVdp *vdp, uint8_t *rgb, size_t size,
                         YsSmsFrameStats *stats) {
    if (!vdp || !rgb || size < YS_SMS_RGB_BYTES) return false;
    if (stats) memset(stats, 0, sizeof(*stats));
    const uint8_t *reg = vdp->registers;
    uint8_t bg_color[3];
    color_rgb(vdp, 16u + (reg[7] & 15u), bg_color);
    for (unsigned pos = 0; pos < YS_SMS_SCREEN_WIDTH * YS_SMS_SCREEN_HEIGHT;
         ++pos)
        memcpy(rgb + pos * 3u, bg_color, 3u);

    /* Mode 4 and display-enable. Timing/mode 224/240 are separate work. */
    if ((reg[0] & 4u) == 0u || (reg[1] & 0x40u) == 0u)
        return true;

    const unsigned table_base = (unsigned)(reg[2] & 0x0Eu) << 10;
    const unsigned sprite_base = (unsigned)(reg[5] & 0x7Eu) << 7;
    const unsigned sprite_pattern = (reg[6] & 4u) ? 0x2000u : 0u;
    const bool tall = (reg[1] & 2u) != 0u;
    const bool zoom = (reg[1] & 1u) != 0u;
    const unsigned sprite_scale = zoom ? 2u : 1u;
    const unsigned sprite_height = (tall ? 16u : 8u) * sprite_scale;
    const unsigned sprite_width = 8u * sprite_scale;

    for (unsigned y = 0; y < YS_SMS_SCREEN_HEIGHT; ++y) {
        uint8_t opaque_priority[YS_SMS_SCREEN_WIDTH] = {0};
        uint8_t occupied_sprite[YS_SMS_SCREEN_WIDTH] = {0};
        unsigned scrolly = (unsigned)((uint8_t)(y - reg[9]));
        for (unsigned x = 0; x < YS_SMS_SCREEN_WIDTH; ++x) {
            unsigned sx = (unsigned)((uint8_t)(x - reg[8]));
            unsigned sy = scrolly;
            if (y < 16u && (reg[0] & 0x40u) != 0u) sx = x;
            if (x >= 248u && (reg[0] & 0x80u) != 0u) sy = y;
            unsigned cell = (sy >> 3) * 32u + (sx >> 3);
            unsigned word = wrap_vram(table_base + 2u * cell);
            unsigned entry = (unsigned)vdp->vram[word] |
                             ((unsigned)vdp->vram[wrap_vram(word + 1u)] << 8);
            unsigned px = sx & 7u, py = sy & 7u;
            if (entry & 0x0200u) px = 7u - px;
            if (entry & 0x0400u) py = 7u - py;
            unsigned index = tile_pixel(vdp, entry & 0x01FFu, px, py, 0u);
            opaque_priority[x] = (uint8_t)((entry & 0x1000u) && index != 0u);
            color_rgb(vdp, index + ((entry & 0x0800u) ? 16u : 0u),
                      rgb + (y * YS_SMS_SCREEN_WIDTH + x) * 3u);
        }
        unsigned count = 0u;
        bool overflow = false;
        for (unsigned sprite = 0; sprite < 64u; ++sprite) {
            unsigned raw_y = vdp->vram[wrap_vram(sprite_base + sprite)];
            if (raw_y == 0xD0u) break; /* 192-line sprite list terminator. */
            unsigned top = (raw_y + 1u) & 255u;
            /* Sprite Y wraps in the 256-line coordinate space. */
            unsigned relative = (y - top) & 255u;
            if (relative >= sprite_height) continue;
            if (++count > 8u) { overflow = true; continue; }
            unsigned pair = sprite_base + 0x80u + sprite * 2u;
            int left = (int)vdp->vram[wrap_vram(pair)];
            if (reg[0] & 8u) left -= 8;
            unsigned tile = vdp->vram[wrap_vram(pair + 1u)];
            if (tall) tile &= ~1u;
            unsigned py = relative / sprite_scale;
            for (unsigned col = 0; col < sprite_width; ++col) {
                int x = left + (int)col;
                if (x < 0 || x >= YS_SMS_SCREEN_WIDTH) continue;
                unsigned sx = (unsigned)x;
                if (reg[0] & 0x20u && sx < 8u) continue;
                unsigned color = tile_pixel(vdp, tile + (py >> 3),
                                             col / sprite_scale, py & 7u,
                                             sprite_pattern);
                if (!color) continue;
                if (occupied_sprite[sx]) {
                    if (stats) ++stats->sprite_collision_pixels;
                    continue; /* Lower-numbered sprites are in front. */
                }
                occupied_sprite[sx] = 1u;
                if (!opaque_priority[sx])
                    color_rgb(vdp, 16u + color,
                              rgb + (y * YS_SMS_SCREEN_WIDTH + sx) * 3u);
            }
        }
        if (stats && overflow) ++stats->sprite_overflow_lines;
        if (reg[0] & 0x20u)
            for (unsigned x = 0; x < 8u; ++x)
                memcpy(rgb + (y * YS_SMS_SCREEN_WIDTH + x) * 3u, bg_color, 3u);
    }
    return true;
}

bool ys_sms_video_write_ppm(FILE *stream, const uint8_t *rgb, size_t size) {
    if (!stream || !rgb || size < YS_SMS_RGB_BYTES) return false;
    if (fprintf(stream, "P6\n%d %d\n255\n", YS_SMS_SCREEN_WIDTH,
                YS_SMS_SCREEN_HEIGHT) < 0) return false;
    return fwrite(rgb, 1, YS_SMS_RGB_BYTES, stream) == YS_SMS_RGB_BYTES;
}
