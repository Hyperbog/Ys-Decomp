/* PC-14 source record -> original $3F00/$3F80 SAT bytes.
   ROM-free native C11 reference oracle; NOT an onscreen Ys player. */
#include "pc_sprite_sat.h"
#include <stdio.h>
#include <stdlib.h>

int main(int argc,char **argv) {
    if(argc!=3) {
        fputs("usage: ys-pc-sprite-sat-dump source-records.bin sat-corpus.bin\n",
              stderr);
        return EXIT_FAILURE;
    }
    FILE *fp=fopen(argv[1],"rb");
    YsPcSpriteRecords *records=malloc(sizeof(*records));
    if(!fp || !records || !ys_pc_sprite_records_load(fp,records)) {
        fputs("PC-14 invalid source sprite-record package\n",stderr);
        if(fp) fclose(fp);
        free(records);
        return EXIT_FAILURE;
    }
    fclose(fp);
    fp=fopen(argv[2],"wb");
    if(!fp) {free(records);return EXIT_FAILURE;}
    static const uint8_t origins[3][2]={{0,0},{17,29},{240,250}};
    unsigned written=0u;
    for(unsigned pair=0;pair<3u;++pair) {
        for(unsigned index=0;index<YS_PC_SPRITE_RECORDS;++index) {
            YsPcSatBuffer sat;
            if(!ys_pc_sprite_stage(records,index,
                                   origins[pair][0],origins[pair][1],&sat) ||
               fwrite(sat.y,1u,sizeof(sat.y),fp)!=sizeof(sat.y) ||
               fwrite(sat.xt,1u,sizeof(sat.xt),fp)!=sizeof(sat.xt)) {
                fputs("PC-14 SAT replay failed\n",stderr);
                fclose(fp);free(records);
                return EXIT_FAILURE;
            }
            written+=YS_PC_SAT_BYTES;
        }
    }
    if(fclose(fp)!=0) {free(records);return EXIT_FAILURE;}
    free(records);
    printf("PASS PC-14 independent native SAT replay: 192 source cases,"
           " %u output bytes (original Phase19 digest checked in CI)\n",written);
    return written==36864u?EXIT_SUCCESS:EXIT_FAILURE;
}
