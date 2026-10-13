#include "sms_video.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void encode_tile(YsSmsVdp *vdp, unsigned number, unsigned y,
                        unsigned x, unsigned color) {
    unsigned offset=number*32u+y*4u;
    unsigned bit=7u-x;
    for(unsigned plane=0;plane<4u;++plane) {
        if (color & (1u<<plane))
            vdp->vram[offset+plane]|=(uint8_t)(1u<<bit);
    }
}
static void init_fixture(YsSmsVdp *vdp) {
    ys_sms_vdp_reset(vdp);
    vdp->registers[0]=4u; /* mode 4, scrolling allowed */
    vdp->registers[1]=0x40u; /* display enabled */
    vdp->registers[2]=0x0Eu; /* name table $3800 */
    vdp->registers[5]=0x7Eu; /* sprites $3F00 */
    vdp->registers[7]=0u;
    vdp->cram[0]=0x00u;
    vdp->cram[1]=0x20u; /* dark sky */
    vdp->cram[2]=0x30u; /* bright blue */
    vdp->cram[3]=0x3Fu; /* white */
    vdp->cram[4]=0x0Cu; /* green */
    vdp->cram[5]=0x08u; /* olive */
    vdp->cram[6]=0x03u; /* red */
    vdp->cram[7]=0x0Fu; /* yellow */
    vdp->cram[16]=0x00u;
    vdp->cram[17]=0x0Fu; /* yellow star */
    vdp->cram[18]=0x3Fu;
    for(unsigned y=0;y<8u;++y) {
        for(unsigned x=0;x<8u;++x) {
            encode_tile(vdp,1u,y,x,1u);
            encode_tile(vdp,2u,y,x,((x+y)&7u)<2u?3u:2u);
            encode_tile(vdp,3u,y,x,y<2u?4u:(x==y?7u:5u));
            encode_tile(vdp,4u,y,x,((x^y)&4u)?4u:5u);
            encode_tile(vdp,5u,y,x,(x==y||x+y==7u)?7u:6u);
            encode_tile(vdp,6u,y,x,
                        (x==3u||x==4u||y==3u||y==4u)?1u:0u);
        }
    }
    for(unsigned row=0;row<24u;++row)
        for(unsigned col=0;col<32u;++col) {
            unsigned id=row<10u?1u:row<15u?2u:row<18u?3u:4u;
            if(row<10u && (col%13u==3u||col%13u==4u)) id=2u;
            if(row>=18u && col%8u==4u) id=5u;
            unsigned word=id;
            unsigned addr=0x3800u+2u*(row*32u+col);
            vdp->vram[addr]=(uint8_t)word;
            vdp->vram[addr+1u]=(uint8_t)(word>>8);
        }
    vdp->vram[0x3F00u]=62u; /* first sprite starts at y=63 */
    vdp->vram[0x3F01u]=0xD0u; /* terminate list */
    vdp->vram[0x3F80u]=120u;
    vdp->vram[0x3F81u]=6u;
}

int main(int argc, char **argv) {
    if(argc!=2) {
        fprintf(stderr,"usage: ys-native-preview output.ppm | --check\n");
        return EXIT_FAILURE;
    }
    YsSmsVdp *vdp=malloc(sizeof(*vdp));
    uint8_t *rgb=malloc(YS_SMS_RGB_BYTES);
    if(!vdp || !rgb) {
        free(vdp);free(rgb);
        fputs("out of memory\n",stderr);
        return EXIT_FAILURE;
    }
    init_fixture(vdp);
    YsSmsFrameStats stats;
    if(!ys_sms_video_render(vdp,rgb,YS_SMS_RGB_BYTES,&stats)) {
        free(vdp);free(rgb);
        fputs("mode-4 diagnostic rendering failed\n",stderr);
        return EXIT_FAILURE;
    }
    if(strcmp(argv[1],"--check")==0) {
        /* Sanity-check observable background and sprite without a ROM. */
        unsigned sky=(10u*YS_SMS_SCREEN_WIDTH+10u)*3u;
        unsigned sprite=(63u*YS_SMS_SCREEN_WIDTH+123u)*3u;
        if(rgb[sky+2u]==0u || rgb[sprite]==0u) {
            free(vdp);free(rgb);
            fputs("diagnostic pixel validation failed\n",stderr);
            return EXIT_FAILURE;
        }
        puts("PASS synthetic SMS mode-4 256x192 renderer (not actual Ys gameplay)");
        free(vdp);free(rgb);
        return EXIT_SUCCESS;
    }
    FILE *out=fopen(argv[1],"wb");
    if(!out) {perror("open preview");free(vdp);free(rgb);return EXIT_FAILURE;}
    bool ok=ys_sms_video_write_ppm(out,rgb,YS_SMS_RGB_BYTES);
    if(fclose(out)!=0) ok=false;
    if(ok) printf("Wrote synthetic SMS video fixture: %s (256x192 PPM)\n",argv[1]);
    else fputs("error writing PPM preview\n",stderr);
    free(vdp);free(rgb);
    return ok?EXIT_SUCCESS:EXIT_FAILURE;
}
