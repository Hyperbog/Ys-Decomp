#include "sms_clock.h"
#include "sms_video.h"
#include "video_fixture.h"
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static bool next_frame(YsSmsClock *clock, YsSmsVdp *vdp,
                       uint8_t *rgb, unsigned index) {
    ys_sms_video_fixture_animate(vdp,index);
    if (!ys_sms_clock_advance(clock,vdp,ys_sms_clock_tstates_per_frame(clock)))
        return false;
    if (clock->frames!=(uint64_t)index+1u || !((vdp->status)&0x80u))
        return false;
    if (!ys_sms_video_render(vdp,rgb,YS_SMS_RGB_BYTES,NULL))
        return false;
    /* Emulate the status-port acknowledgment by a caller; not CPU gameplay. */
    uint8_t status=0u;
    if(!ys_sms_vdp_read(vdp,0xBF,&status) || (status&0x80u)==0u)
        return false;
    return vdp->status==0;
}
static uint32_t hash_frame(const uint8_t *rgb) {
    uint32_t hash=2166136261u; /* Simple diagnostic FNV-1a; not a signature. */
    for(size_t i=0;i<YS_SMS_RGB_BYTES;++i) {
        hash^=rgb[i];
        hash*=16777619u;
    }
    return hash;
}

int main(int argc, char **argv) {
    bool check=argc==2 && strcmp(argv[1],"--check")==0;
    if(!check && (argc<3 || argc>4)) {
        fputs("usage: ys-native-frames output-prefix N [ntsc|pal]\n"
              "       ys-native-frames --check\n",stderr);
        return EXIT_FAILURE;
    }
    unsigned count=3u;
    YsSmsRegion region=YS_SMS_NTSC;
    if(!check) {
        if(argv[2][0]=='-' || !argv[2][0]) {
            fputs("frame count must be 1..120\n",stderr);
            return EXIT_FAILURE;
        }
        errno=0;
        char *end=NULL;
        unsigned long parsed=strtoul(argv[2],&end,10);
        if(errno || !end || *end || parsed<1u || parsed>120u) {
            fputs("frame count must be 1..120\n",stderr);
            return EXIT_FAILURE;
        }
        count=(unsigned)parsed;
        if(argc==4) {
            if(strcmp(argv[3],"pal")==0) region=YS_SMS_PAL;
            else if(strcmp(argv[3],"ntsc")!=0) {
                fputs("region must be ntsc or pal\n",stderr);
                return EXIT_FAILURE;
            }
        }
    }
    YsSmsVdp *vdp=malloc(sizeof(*vdp));
    uint8_t *rgb=malloc(YS_SMS_RGB_BYTES);
    size_t filename_size=check?1u:strlen(argv[1])+32u;
    char *filename=malloc(filename_size);
    if(!vdp || !rgb || !filename) {
        fputs("out of memory\n",stderr);
        free(vdp);free(rgb);free(filename);
        return EXIT_FAILURE;
    }
    ys_sms_video_fixture_init(vdp);
    /* Enabled frame-IRQ output is observable via ys_sms_clock_vblank_irq,
       but this demo deliberately has NO synthetic Z80 instruction stream. */
    vdp->registers[1] |= 0x20u;
    YsSmsClock clock;
    if(!ys_sms_clock_reset(&clock,region)) {
        free(vdp);free(rgb);free(filename);return EXIT_FAILURE;
    }
    uint32_t first_hash=0u;
    bool different=false,ok=true;
    for(unsigned i=0;i<count;++i) {
        if(!next_frame(&clock,vdp,rgb,i)) {ok=false;break;}
        uint32_t hash=hash_frame(rgb);
        if(i==0) first_hash=hash;
        else if(hash!=first_hash) different=true;
        if(!check) {
            int written=snprintf(filename,filename_size,"%s-%03u.ppm",argv[1],i);
            if(written<0 || (size_t)written>=filename_size) {ok=false;break;}
            FILE *out=fopen(filename,"wb");
            if(!out) {perror("open frame");ok=false;break;}
            bool stored=ys_sms_video_write_ppm(out,rgb,YS_SMS_RGB_BYTES);
            if(fclose(out)!=0) stored=false;
            if(!stored) {fputs("could not write frame\n",stderr);ok=false;break;}
        }
    }
    if(check && (!different || clock.frames!=count ||
                 clock.vblank_events!=count)) ok=false;
    if(ok) printf("PASS %u synthetic %s frames, %llu VBlank events"
                  " (not actual Ys frames)\n",
                  count,region==YS_SMS_NTSC?"NTSC":"PAL",
                  (unsigned long long)clock.vblank_events);
    free(vdp);free(rgb);free(filename);
    return ok?EXIT_SUCCESS:EXIT_FAILURE;
}
