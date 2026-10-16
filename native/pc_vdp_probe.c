/* Inspect a REAL original M44 frame checkpoint, not playable Ys. */
#include "pc_vdp_checkpoint.h"
#include "sms_video.h"
#include <stdio.h>
#include <stdlib.h>

int main(int argc,char **argv) {
    if(argc!=4 && argc!=5) {
        fputs("usage: ys-pc-vdp-probe M44.vdp M44-patterns.bin M43-nametable.bin [preview.ppm]\n",stderr);
        return EXIT_FAILURE;
    }
    FILE *fp=fopen(argv[1],"rb");
    YsPcVdpCheckpoint *capture=malloc(sizeof(*capture));
    YsPcPatterns *patterns=malloc(sizeof(*patterns));
    YsPcNameTable *names=malloc(sizeof(*names));
    if(!capture || !patterns || !names || !fp ||
       !ys_pc_vdp_checkpoint_load(fp,capture)) {
        fputs("PC-8 checkpoint absent/corrupt\n",stderr);
        if(fp) fclose(fp);
        free(capture);free(patterns);free(names);return EXIT_FAILURE;
    }
    fclose(fp);
    fp=fopen(argv[2],"rb");
    bool pattern_ok=fp && ys_pc_patterns_load(fp,patterns);
    if(fp) fclose(fp);
    fp=fopen(argv[3],"rb");
    bool names_ok=fp && ys_pc_nametable_load(fp,names);
    if(fp) fclose(fp);
    if(!pattern_ok || !names_ok ||
       !ys_pc_vdp_checkpoint_matches(capture,patterns,names)) {
        fputs("PC-8 M44 concurrent source pattern/name-table identity mismatch\n",stderr);
        free(capture);free(patterns);free(names);return EXIT_FAILURE;
    }
    const YsSmsVdp *v=&capture->vdp;
    bool display=(v->registers[0]&4u)!=0u &&
                 (v->registers[1]&0x40u)!=0u;
    printf("PASS PC-8 M44 simultaneous source VDP: PC=$%04X"
           " patterns=12288/12288 names=1536/1536 CRAM=32 registers=16"
           " R0=%02X R1=%02X display=%s\n",
           capture->source_pc,v->registers[0],v->registers[1],
           display?"enabled":"disabled");
    for(unsigned row=0;row<4u;++row) {
        printf("PC-8 authentic CRAM raw %02u-%02u:",row*8u,row*8u+7u);
        for(unsigned col=0;col<8u;++col)
            printf(" %02X",v->cram[row*8u+col]);
        putchar('\n');
    }
    if(argc==5) {
        uint8_t *rgb=malloc(YS_SMS_RGB_BYTES);
        if(!rgb || !ys_sms_video_render(v,rgb,YS_SMS_RGB_BYTES,NULL)) {
            fputs("PC-8 VDP rendering failed\n",stderr);
            free(rgb);free(capture);free(patterns);free(names);
            return EXIT_FAILURE;
        }
        fp=fopen(argv[4],"wb");
        bool ok=fp && ys_sms_video_write_ppm(fp,rgb,YS_SMS_RGB_BYTES);
        if(fp && fclose(fp)!=0) ok=false;
        free(rgb);
        if(!ok) {
            fputs("PC-8 VDP PPM write failed\n",stderr);
            free(capture);free(patterns);free(names);
            return EXIT_FAILURE;
        }
        puts("PASS PC-8 rendered actual snapshot through existing diagnostic"
             " SMS VDP renderer; not validated original-game playable scene");
    }
    free(capture);free(patterns);free(names);
    return EXIT_SUCCESS;
}
