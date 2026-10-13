#include "sms_video.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static YsSmsVdp v;
static uint8_t frame[YS_SMS_RGB_BYTES];

static void tile_plane(unsigned number, unsigned row, unsigned plane,
                       uint8_t bits) {
    v.vram[number * 32u + row * 4u + plane] = bits;
}
static void fill_tile(unsigned number, unsigned color) {
    for(unsigned y=0;y<8u;++y)
        for(unsigned plane=0;plane<4u;++plane)
            tile_plane(number,y,plane,
                       (color & (1u << plane)) ? 0xFFu : 0u);
}
static void name_entry(unsigned cellx, unsigned celly, uint16_t entry) {
    unsigned addr=0x3800u+2u*(celly*32u+cellx);
    v.vram[addr]=(uint8_t)entry;
    v.vram[addr+1u]=(uint8_t)(entry>>8);
}
static void setup(void) {
    ys_sms_vdp_reset(&v);
    v.registers[0]=4u;    /* mode 4 */
    v.registers[1]=0x40u; /* display enabled */
    v.registers[2]=0x0Eu; /* name table $3800 */
    v.registers[5]=0x7Eu; /* sprite attributes $3F00 */
    v.vram[0x3F00]=0xD0u;
    v.cram[0]=0x00u;
    v.cram[1]=0x03u; /* red */
    v.cram[2]=0x0Cu; /* green */
    v.cram[3]=0x30u; /* blue */
    v.cram[4]=0x3Fu; /* white */
    v.cram[16]=0x00u;
    v.cram[17]=0x30u; /* blue sprite */
    v.cram[18]=0x0Fu; /* yellow sprite */
    v.cram[19]=0x03u; /* red sprite */
}
static void check_pixel(unsigned x,unsigned y,
                        unsigned r,unsigned g,unsigned b) {
    const uint8_t *p=frame+3u*(y*YS_SMS_SCREEN_WIDTH+x);
    if (p[0]!=r || p[1]!=g || p[2]!=b)
        fprintf(stderr,"pixel (%u,%u) got RGB=%u,%u,%u expected=%u,%u,%u\n",
                x,y,p[0],p[1],p[2],r,g,b);
    assert(p[0]==r && p[1]==g && p[2]==b);
}
static void draw(void) {
    assert(ys_sms_video_render(&v,frame,sizeof(frame),NULL));
}

static void test_disabled_display_and_cram(void) {
    setup();
    v.registers[1]=0u;
    v.registers[7]=1u;
    v.cram[17]=0x39u; /* red=1 green=2 blue=3 */
    memset(frame,0x7Fu,sizeof(frame));
    YsSmsFrameStats stats={123u,456u};
    assert(ys_sms_video_render(&v,frame,sizeof(frame),&stats));
    check_pixel(0,0,85,170,255);
    check_pixel(255,191,85,170,255);
    assert(stats.sprite_overflow_lines==0 && stats.sprite_collision_pixels==0);
    assert(!ys_sms_video_render(&v,frame,sizeof(frame)-1u,NULL));
    assert(!ys_sms_video_render(NULL,frame,sizeof(frame),NULL));
    assert(!ys_sms_video_render(&v,NULL,sizeof(frame),NULL));
}
static void test_tile_planes_flip_and_palettes(void) {
    setup();
    fill_tile(1,1);
    fill_tile(2,2);
    fill_tile(3,3);
    name_entry(0,0,1u);
    name_entry(1,0,2u|0x0800u); /* palette 1 */
    name_entry(2,0,3u|0x1000u); /* high priority */
    tile_plane(4,0,0,0x80u); /* one source pixel at upper left */
    name_entry(3,0,4u|0x0600u); /* horizontal and vertical flips */
    draw();
    check_pixel(0,0,255,0,0);
    check_pixel(7,7,255,0,0);
    check_pixel(8,0,255,255,0); /* palette 1 index 2 */
    check_pixel(16,0,0,0,255); /* palette 0 index 3: blue */
    check_pixel(24,0,0,0,0);
    check_pixel(31,7,255,0,0);
    check_pixel(31,0,0,0,0);
    check_pixel(255,191,0,0,0);
}
static void test_priority_collision_and_sprite_order(void) {
    setup();
    fill_tile(1,1);
    fill_tile(2,2);
    fill_tile(3,1);
    fill_tile(4,2);
    name_entry(0,0,1u);
    name_entry(1,0,2u|0x1000u);
    v.vram[0x3F00u]=0xFFu; /* top y=0 */
    v.vram[0x3F01u]=0xFFu; /* second sprite overlaps */
    v.vram[0x3F02u]=0xD0u; /* terminate */
    v.vram[0x3F80u]=6u; v.vram[0x3F81u]=3u;
    v.vram[0x3F82u]=7u; v.vram[0x3F83u]=4u;
    v.status=0xAAu;
    YsSmsFrameStats stats;
    assert(ys_sms_video_render(&v,frame,sizeof(frame),&stats));
    check_pixel(5,0,255,0,0); /* background */
    check_pixel(6,0,0,0,255); /* sprite 0 above BG */
    check_pixel(7,0,0,0,255); /* sprite 0 above sprite 1 */
    check_pixel(8,0,0,255,0); /* priority BG blocks both sprites */
    check_pixel(14,0,0,255,0); /* sprite 1 also blocked by BG */
    assert(stats.sprite_collision_pixels==7u*8u);
    assert(stats.sprite_overflow_lines==0);
    assert(v.status==0xAAu); /* renderer has no IRQ/status side effects */
}
static void test_eight_sprite_scanline_limit(void) {
    setup();
    fill_tile(1,1);
    for(unsigned i=0;i<9u;++i) {
        v.vram[0x3F00u+i]=0xFFu;
        v.vram[0x3F80u+i*2u]=(uint8_t)(i*12u);
        v.vram[0x3F81u+i*2u]=1u;
    }
    v.vram[0x3F09u]=0xD0u;
    YsSmsFrameStats stats;
    assert(ys_sms_video_render(&v,frame,sizeof(frame),&stats));
    check_pixel(84,0,0,0,255); /* sprite 7 is visible */
    check_pixel(96,0,0,0,0); /* sprite 8 not rendered */
    assert(stats.sprite_overflow_lines==8u);
    assert(stats.sprite_collision_pixels==0);
}
static void test_scroll_mask_and_tall_zoom(void) {
    setup();
    fill_tile(1,1);
    fill_tile(2,2);
    name_entry(0,0,1u);
    name_entry(1,0,2u);
    v.registers[8]=8u;
    draw();
    check_pixel(8,0,255,0,0);
    check_pixel(16,0,0,255,0);
    v.registers[0]|=0x40u; /* freeze top two tile rows */
    draw();
    check_pixel(0,0,255,0,0);
    v.registers[0]|=0x20u; /* blank left 8 columns */
    v.registers[7]=3u;
    draw();
    check_pixel(0,0,255,0,0); /* CRAM[19] is red backdrop */
    check_pixel(8,0,0,255,0);
    setup();
    fill_tile(6,1);
    fill_tile(7,2);
    v.registers[1]|=3u; /* double-sized 8x16 sprite */
    v.vram[0x3F00u]=0xFFu;
    v.vram[0x3F01u]=0xD0u;
    v.vram[0x3F80u]=10u;
    v.vram[0x3F81u]=7u; /* tall sprite aligns to even tile 6 */
    draw();
    check_pixel(10,0,0,0,255);
    check_pixel(25,15,0,0,255);
    check_pixel(10,16,255,255,0);
    check_pixel(25,31,255,255,0);
    check_pixel(10,32,0,0,0);
}
static void test_binary_ppm(void) {
    setup();
    draw();
    FILE *file=tmpfile();
    assert(file);
    assert(ys_sms_video_write_ppm(file,frame,sizeof(frame)));
    assert(!ys_sms_video_write_ppm(file,frame,sizeof(frame)-1u));
    assert(!ys_sms_video_write_ppm(NULL,frame,sizeof(frame)));
    assert(fseek(file,0,SEEK_END)==0);
    long length=ftell(file);
    assert(length==(long)YS_SMS_RGB_BYTES+15L);
    assert(fseek(file,0,SEEK_SET)==0);
    char header[16]={0};
    assert(fread(header,1,15,file)==15u);
    assert(memcmp(header,"P6\n256 192\n255\n",15u)==0);
    fclose(file);
}
int main(void) {
    test_disabled_display_and_cram();
    test_tile_planes_flip_and_palettes();
    test_priority_collision_and_sprite_order();
    test_eight_sprite_scanline_limit();
    test_scroll_mask_and_tall_zoom();
    test_binary_ppm();
    puts("PASS: SMS mode-4 RGB palette, tile flips, scroll, sprite priority, scanline limit and PPM");
    return 0;
}
