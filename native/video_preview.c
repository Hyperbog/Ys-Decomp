#include "sms_video.h"
#include "video_fixture.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>


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
    ys_sms_video_fixture_init(vdp);
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
