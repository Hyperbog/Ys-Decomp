#include "pc_tiles.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

enum { RAW_BYTES=YS_PC_TILE_COUNT*YS_PC_TILE_BYTES };
static void write_fixture(FILE *fp,uint8_t raw[RAW_BYTES],int corrupt) {
    uint8_t header[16]={
        'Y','S','P','C','4','T','0','1',0xB0,0,0,0,
        0xE2,0x7D,0xDA,0xB9
    }; /* Known CRC32 of 5632 zero bytes: 0xB9DA7DE2. */
    if(corrupt) raw[0]=0x80u;
    assert(fwrite(header,1,sizeof(header),fp)==sizeof(header));
    assert(fwrite(raw,1,RAW_BYTES,fp)==RAW_BYTES);
    rewind(fp);
}
static void test_decode_and_grayscale(void) {
    uint8_t raw[RAW_BYTES]={0};
    YsPcTiles tiles;
    assert(!ys_pc_tiles_decode(NULL,RAW_BYTES,&tiles));
    assert(!ys_pc_tiles_decode(raw,RAW_BYTES-1u,&tiles));
    for(unsigned plane=0;plane<4u;++plane)
        raw[plane]=0x80u;
    raw[4u]=0x01u; /* bottom of second row: plane zero at x=7. */
    assert(ys_pc_tiles_decode(raw,RAW_BYTES,&tiles));
    assert(tiles.index[0][0]==15u && tiles.index[0][1]==0u);
    assert(tiles.index[0][8u+7u]==1u);
    assert(tiles.index[1][0]==0u && tiles.index[175][63]==0u);
    uint8_t rgb[YS_PC_ATLAS_W*YS_PC_ATLAS_H*3];
    memset(rgb,0xAA,sizeof(rgb));
    ys_pc_tiles_grayscale(&tiles,rgb);
    assert(rgb[0]==255u && rgb[1]==255u && rgb[2]==255u);
    assert(rgb[3]==0u && rgb[4]==0u && rgb[5]==0u);
    size_t offset=((size_t)1*YS_PC_ATLAS_W+7u)*3u;
    assert(rgb[offset]==17u && rgb[offset+1u]==17u);
    assert(rgb[sizeof(rgb)-1u]==0u);
}
static void test_crc_file(void) {
    uint8_t raw[RAW_BYTES]={0};
    YsPcTiles tiles;
    FILE *valid=tmpfile();
    assert(valid);
    write_fixture(valid,raw,0);
    assert(ys_pc_tiles_load(valid,&tiles));
    assert(tiles.index[0][0]==0u && tiles.index[175][63]==0u);
    fclose(valid);
    FILE *damaged=tmpfile();
    assert(damaged);
    write_fixture(damaged,raw,1);
    assert(!ys_pc_tiles_load(damaged,&tiles));
    fclose(damaged);
}
int main(void) {
    test_decode_and_grayscale();
    test_crc_file();
    puts("PASS PC-1: 176 tiles, 4-plane decode, grayscale, CRC rejection");
    return 0;
}
