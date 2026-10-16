#include "pc_vdp_checkpoint.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static YsSmsVdp vdp;
static YsPcVdpCheckpoint loaded;
static YsPcPatterns patterns;
static YsPcNameTable names;

static bool load_bytes(FILE *source,YsPcVdpCheckpoint *target) {
    rewind(source);
    return ys_pc_vdp_checkpoint_load(source,target);
}
static void basic(void) {
    memset(&vdp,0,sizeof(vdp));
    memset(&patterns,0,sizeof(patterns));
    memset(&names,0,sizeof(names));
    for(unsigned i=0;i<YS_VRAM_BYTES;++i) vdp.vram[i]=(uint8_t)(i*37u);
    for(unsigned i=0;i<YS_CRAM_BYTES;++i) vdp.cram[i]=(uint8_t)(i*3u);
    for(unsigned i=0;i<YS_VDP_REGISTERS;++i)
        vdp.registers[i]=(uint8_t)(i*11u);
    memcpy(patterns.raw,vdp.vram,YS_PC_PATTERN_BYTES);
    memcpy(names.raw,vdp.vram+YS_PC_NT_VRAM_START,YS_PC_NT_RAW_SIZE);

    FILE *f=tmpfile();
    assert(f);
    assert(!ys_pc_vdp_checkpoint_save(NULL,&vdp,0x0C87u));
    assert(!ys_pc_vdp_checkpoint_save(f,NULL,0x0C87u));
    assert(!ys_pc_vdp_checkpoint_save(f,&vdp,0x0C92u));
    assert(ys_pc_vdp_checkpoint_save(f,&vdp,YS_PC_VDP_CHECKPOINT_PC));
    assert(ftell(f)==YS_PC_VDP_FILE_BYTES);
    assert(load_bytes(f,&loaded));
    assert(loaded.source_pc==0x0C87u);
    assert(memcmp(loaded.vdp.vram,vdp.vram,YS_VRAM_BYTES)==0);
    assert(memcmp(loaded.vdp.cram,vdp.cram,YS_CRAM_BYTES)==0);
    assert(memcmp(loaded.vdp.registers,vdp.registers,YS_VDP_REGISTERS)==0);
    assert(ys_pc_vdp_checkpoint_matches(&loaded,&patterns,&names));
    assert(!ys_pc_vdp_checkpoint_matches(NULL,&patterns,&names));
    assert(!ys_pc_vdp_checkpoint_matches(&loaded,NULL,&names));
    assert(!ys_pc_vdp_checkpoint_matches(&loaded,&patterns,NULL));
    patterns.raw[0]^=1u;
    assert(!ys_pc_vdp_checkpoint_matches(&loaded,&patterns,&names));
    patterns.raw[0]^=1u;
    names.raw[1]^=1u;
    assert(!ys_pc_vdp_checkpoint_matches(&loaded,&patterns,&names));
    names.raw[1]^=1u;
    loaded.source_pc=0x0C92u;
    assert(!ys_pc_vdp_checkpoint_matches(&loaded,&patterns,&names));
    loaded.source_pc=0x0C87u;

    /* Valid CRC alone is insufficient: source-backed asset comparison
       rejects a coherent but different VDP frame. */
    vdp.vram[0]^=1u;
    FILE *different=tmpfile();
    assert(different);
    assert(ys_pc_vdp_checkpoint_save(different,&vdp,0x0C87u));
    assert(load_bytes(different,&loaded));
    assert(!ys_pc_vdp_checkpoint_matches(&loaded,&patterns,&names));
    fclose(different);

    rewind(f);
    assert(fputc('X',f)!=EOF);
    assert(!load_bytes(f,&loaded));
    rewind(f);
    assert(fwrite("YSPC8V01",1u,8u,f)==8u);
    assert(fseek(f,16u+123u,SEEK_SET)==0);
    assert(fputc('Y',f)!=EOF);
    assert(!load_bytes(f,&loaded));
    fclose(f);
}
int main(void) {
    basic();
    puts("PASS PC-8: simultaneous M44 VRAM+CRAM+register snapshot,"
         " exact source-match guard, CRC/bounds/magic/PC");
    return 0;
}
