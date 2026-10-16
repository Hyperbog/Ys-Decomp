#include "pc_records.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
enum { HEADER=16, META=22*6, N=YS_PC_RECORD_FILE_BYTES };
static uint8_t packet[N];
static const uint16_t counts[22]={
    16,15,15,3,0,13,12,13,13,10,10,12,4,9,11,5,3,13,9,12,10,1
};
static uint32_t crc32_bytes(const uint8_t *raw,size_t n) {
    uint32_t crc=0xFFFFFFFFu;
    for(size_t i=0;i<n;++i) {
        crc^=raw[i];
        for(unsigned k=0;k<8u;++k)
            crc=(crc>>1)^(0xEDB88320u&(0u-(crc&1u)));
    }
    return ~crc;
}
static void set16(unsigned at,unsigned v) {
    packet[at]=(uint8_t)v;
    packet[at+1]=(uint8_t)(v>>8);
}
static void checksum(void) {
    uint32_t crc=crc32_bytes(packet+HEADER,N-HEADER);
    for(unsigned i=0;i<4;++i) packet[12u+i]=(uint8_t)(crc>>(i*8u));
}
static void prepare(void) {
    memset(packet,0,sizeof(packet));
    memcpy(packet,"YSPC7M01",8u);
    set16(8,22u);set16(10,209u);
    unsigned addr=0xBA67u,total=0u,terms=0u;
    for(unsigned i=0;i<22;++i) {
        unsigned term=(i!=0u && i!=3u);
        unsigned offset=HEADER+6u*i;
        set16(offset,addr);
        set16(offset+2u,counts[i]);
        packet[offset+4u]=(uint8_t)term;
        addr+=counts[i]*4u+term;
        total+=counts[i];terms+=term;
    }
    assert(addr==0xBDBFu && total==209u && terms==20u);
    for(unsigned i=0;i<836u;++i) packet[HEADER+META+i]=(uint8_t)(i*17u);
    for(unsigned i=0;i<16u;++i) packet[HEADER+META+836u+i]=(uint8_t)(i+3u);
    checksum();
}
static bool load_packet(size_t amount,YsPcRecords *out) {
    FILE *f=tmpfile();
    assert(f);
    assert(fwrite(packet,1,amount,f)==amount);
    rewind(f);
    bool ok=ys_pc_records_load(f,out);
    fclose(f);
    return ok;
}
int main(void) {
    YsPcRecords records;
    prepare();
    assert(ys_pc_records_start(NULL,0u)==0u);
    assert(load_packet(N,&records));
    assert(records.groups[0].source_pc==0xBA67u &&
           records.groups[0].count==16u &&
           !records.groups[0].terminator_zero);
    assert(records.groups[4].count==0u &&
           records.groups[4].terminator_zero);
    assert(records.groups[21].source_pc==0xBDBAu &&
           records.groups[21].count==1u);
    assert(ys_pc_records_start(&records,1u)==16u);
    assert(ys_pc_records_start(&records,21u)==208u);
    assert(ys_pc_records_start(&records,22u)==0u);
    assert(records.records[0][1]==17u &&
           records.records[208][3]==(uint8_t)(835u*17u));
    assert(records.staging[0]==3u && records.staging[15]==18u);
    assert(!load_packet(N-1u,&records));
    packet[0]='Z';assert(!load_packet(N,&records));
    prepare();
    packet[HEADER+META+12u]^=0x01u;assert(!load_packet(N,&records));
    prepare();
    set16(HEADER+2u,15u);
    checksum();assert(!load_packet(N,&records)); /* semantic boundary */
    prepare();
    packet[HEADER+4u]=2u;
    checksum();assert(!load_packet(N,&records)); /* invalid termination */
    prepare();
    packet[HEADER+5u]=1u;
    checksum();assert(!load_packet(N,&records)); /* reserved byte */
    puts("PASS PC-2 bank7 tuple group loader: 22 pointers, 209 records, CRC and boundaries");
    return 0;
}
