#include "pc_vdp_checkpoint.h"
#include <string.h>

static uint32_t crc32_bytes(const uint8_t *src,size_t size) {
    uint32_t crc=0xFFFFFFFFu;
    for(size_t i=0;i<size;++i) {
        crc^=src[i];
        for(unsigned bit=0;bit<8u;++bit)
            crc=(crc>>1)^(0xEDB88320u&(0u-(crc&1u)));
    }
    return ~crc;
}
static uint16_t le16(const uint8_t *p) {
    return (uint16_t)((unsigned)p[0]|((unsigned)p[1]<<8u));
}
static uint32_t le32(const uint8_t *p) {
    return (uint32_t)p[0]|((uint32_t)p[1]<<8u)|
           ((uint32_t)p[2]<<16u)|((uint32_t)p[3]<<24u);
}
static void set16(uint8_t *p,unsigned v) {
    p[0]=(uint8_t)v;p[1]=(uint8_t)(v>>8u);
}
static void set32(uint8_t *p,uint32_t v) {
    for(unsigned k=0;k<4u;++k) p[k]=(uint8_t)(v>>(k*8u));
}
bool ys_pc_vdp_checkpoint_save(FILE *file,const YsSmsVdp *vdp,uint16_t pc) {
    if(!file || !vdp || pc!=YS_PC_VDP_CHECKPOINT_PC) return false;
    uint8_t head[16]={'Y','S','P','C','8','V','0','1'};
    uint32_t crc=0xFFFFFFFFu;
    const uint8_t *sources[3]={vdp->vram,vdp->cram,vdp->registers};
    const size_t sizes[3]={YS_VRAM_BYTES,YS_CRAM_BYTES,YS_VDP_REGISTERS};
    for(unsigned section=0;section<3u;++section)
        for(size_t i=0;i<sizes[section];++i) {
            crc^=sources[section][i];
            for(unsigned bit=0;bit<8u;++bit)
                crc=(crc>>1)^(0xEDB88320u&(0u-(crc&1u)));
        }
    set16(head+8u,pc);
    set16(head+10u,YS_PC_VDP_PAYLOAD_BYTES);
    set32(head+12u,~crc);
    if(fwrite(head,1,sizeof(head),file)!=sizeof(head)) return false;
    for(unsigned section=0;section<3u;++section)
        if(fwrite(sources[section],1,sizes[section],file)!=sizes[section])
            return false;
    return true;
}
bool ys_pc_vdp_checkpoint_load(FILE *file,YsPcVdpCheckpoint *out) {
    if(!file || !out) return false;
    uint8_t header[16];
    /* Untrusted snapshot bytes are bounded to exactly one VDP memory image. */
    uint8_t bytes[YS_PC_VDP_PAYLOAD_BYTES];
    static const uint8_t magic[8]={'Y','S','P','C','8','V','0','1'};
    if(fread(header,1,sizeof(header),file)!=sizeof(header) ||
       memcmp(header,magic,sizeof(magic))!=0 ||
       le16(header+8u)!=YS_PC_VDP_CHECKPOINT_PC ||
       le16(header+10u)!=YS_PC_VDP_PAYLOAD_BYTES ||
       fread(bytes,1,sizeof(bytes),file)!=sizeof(bytes) ||
       fgetc(file)!=EOF ||
       le32(header+12u)!=crc32_bytes(bytes,sizeof(bytes)))
        return false;
    YsPcVdpCheckpoint tmp;
    memset(&tmp,0,sizeof(tmp));
    tmp.source_pc=le16(header+8u);
    memcpy(tmp.vdp.vram,bytes,YS_VRAM_BYTES);
    memcpy(tmp.vdp.cram,bytes+YS_VRAM_BYTES,YS_CRAM_BYTES);
    memcpy(tmp.vdp.registers,bytes+YS_VRAM_BYTES+YS_CRAM_BYTES,
           YS_VDP_REGISTERS);
    *out=tmp;
    return true;
}
bool ys_pc_vdp_checkpoint_matches(const YsPcVdpCheckpoint *capture,
                                   const YsPcPatterns *patterns,
                                   const YsPcNameTable *names) {
    if(!capture || !patterns || !names ||
       capture->source_pc!=YS_PC_VDP_CHECKPOINT_PC) return false;
    return memcmp(capture->vdp.vram,patterns->raw,YS_PC_PATTERN_BYTES)==0 &&
           memcmp(capture->vdp.vram+YS_PC_NT_VRAM_START,
                  names->raw,YS_PC_NT_RAW_SIZE)==0;
}
