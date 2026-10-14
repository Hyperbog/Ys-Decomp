#include "pc_nametable.h"
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static uint8_t buffer[YS_PC_NT_PACKAGE_BYTES];
static uint32_t checksum(const uint8_t *data,size_t size) {
    uint32_t crc=0xFFFFFFFFu;
    for(size_t i=0;i<size;++i) {
        crc^=data[i];
        for(unsigned k=0;k<8u;++k)
            crc=(crc>>1)^(0xEDB88320u&(0u-(crc&1u)));
    }
    return ~crc;
}
static void fix_crc(void) {
    uint32_t crc=checksum(buffer+16u,YS_PC_NT_RAW_SIZE);
    for(unsigned k=0;k<4u;++k)
        buffer[12u+k]=(uint8_t)(crc>>(8u*k));
}
static void prepare(void) {
    memset(buffer,0,sizeof(buffer));
    memcpy(buffer,"YSPC6N01",8u);
    buffer[9]=0x39u;buffer[11]=0x06u;
    buffer[16u]=0x23u;buffer[17u]=0x1Fu; /* pattern 0x123; flip/pal/priority */
    buffer[18u]=0xFFu;buffer[19u]=0x01u; /* pattern 511, no flags */
    buffer[16u+YS_PC_NT_RAW_SIZE-2u]=0x55u;
    buffer[16u+YS_PC_NT_RAW_SIZE-1u]=0x0Au; /* pattern 0x055, H/pal */
    fix_crc();
}
static bool try_load(size_t count,YsPcNameTable *out) {
    FILE *fp=tmpfile();
    assert(fp);
    assert(fwrite(buffer,1,count,fp)==count);
    rewind(fp);
    bool ok=ys_pc_nametable_load(fp,out);
    fclose(fp);
    return ok;
}
static void test_synthetic(void) {
    YsPcNameTable table;
    YsPcNameCell cell;
    prepare();
    assert(!ys_pc_nametable_load(NULL,&table));
    assert(try_load(sizeof(buffer),&table));
    assert(ys_pc_nametable_cell(&table,0u,0u,&cell));
    assert(cell.raw==0x1F23u && cell.pattern==0x123u &&
           cell.horizontal_flip && cell.vertical_flip &&
           cell.palette_1 && cell.priority);
    assert(ys_pc_nametable_cell(&table,1u,0u,&cell));
    assert(cell.pattern==511u && !cell.palette_1 &&
           !cell.horizontal_flip && !cell.vertical_flip &&
           !cell.priority);
    assert(ys_pc_nametable_cell(&table,31u,23u,&cell));
    assert(cell.raw==0x0A55u && cell.pattern==0x55u &&
           cell.horizontal_flip && !cell.vertical_flip &&
           cell.palette_1 && !cell.priority);
    assert(!ys_pc_nametable_cell(&table,32u,0u,&cell));
    assert(!ys_pc_nametable_cell(&table,0u,24u,&cell));
    assert(!ys_pc_nametable_cell(NULL,0u,0u,&cell));
    assert(!ys_pc_nametable_cell(&table,0u,0u,NULL));
    assert(!try_load(sizeof(buffer)-1u,&table));
    buffer[0]='Q';assert(!try_load(sizeof(buffer),&table));
    prepare();
    buffer[9]=0x38u;fix_crc();assert(!try_load(sizeof(buffer),&table));
    prepare();
    buffer[10]=1u;fix_crc();assert(!try_load(sizeof(buffer),&table));
    prepare();
    buffer[100u]^=0x80u;assert(!try_load(sizeof(buffer),&table));
}
static void test_source_package(const char *path) {
    FILE *fp=fopen(path,"rb");
    assert(fp);
    YsPcNameTable table;
    assert(ys_pc_nametable_load(fp,&table));
    fclose(fp);
    YsPcNameCell cell;
    unsigned seen=0u;
    for(unsigned row=0;row<YS_PC_NT_H;++row)
        for(unsigned col=0;col<YS_PC_NT_W;++col) {
            assert(ys_pc_nametable_cell(&table,col,row,&cell));
            size_t i=((size_t)row*YS_PC_NT_W+col)*2u;
            assert(cell.raw==(uint16_t)((unsigned)table.raw[i]|
                   ((unsigned)table.raw[i+1]<<8u)));
            assert(cell.pattern==(cell.raw&0x1FFu));
            ++seen;
        }
    assert(seen==768u);
    puts("PASS PC-6: 768 original source-derived VRAM name entries decoded without guessed palette");
}
int main(int argc,char **argv) {
    assert(argc==1 || argc==2);
    test_synthetic();
    if(argc==2) test_source_package(argv[1]);
    puts("PASS PC-6: original 24x32 lower name-table region, attr flags, CRC/header rejection");
    return 0;
}
