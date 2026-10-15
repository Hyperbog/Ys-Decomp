#include "pc_sprite_selector.h"
bool ys_pc_sprite_selector_source(const YsPcSpriteSelectorInput *in,
                                  uint8_t *raw_c199) {
    if(!in || !raw_c199 || !in->c198 || (in->c011&0x40u))
        return false;
    const unsigned row=((unsigned)in->c184+in->c210)&7u;
    const unsigned col=((unsigned)in->c182+in->c211)&7u;
    *raw_c199=(uint8_t)(0x80u|(row<<3u)|col);
    return true;
}
bool ys_pc_sprite_selector_index(uint8_t raw_c199,unsigned *index) {
    if(!index || raw_c199<0x80u || raw_c199>0xBFu)
        return false;
    const unsigned effective=((unsigned)raw_c199<<1u)&255u;
    *index=effective>>1u;
    return *index<64u;
}

bool ys_pc_sprite_stage_source_state(
    const YsPcSpriteRecords *records,const YsPcSpriteSelectorInput *state,
    YsPcSatBuffer *out,uint8_t *raw_c199,unsigned *directory_index) {
    if(!records || !state || !out || !raw_c199 || !directory_index)
        return false;
    uint8_t selected=0u;
    unsigned index=0u;
    YsPcSatBuffer staged;
    if(!ys_pc_sprite_selector_source(state,&selected) ||
       !ys_pc_sprite_selector_index(selected,&index) ||
       !ys_pc_sprite_stage(records,index,state->c210,state->c211,&staged))
        return false;
    *out=staged;
    *raw_c199=selected;
    *directory_index=index;
    return true;
}
