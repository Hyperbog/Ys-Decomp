#include "pc_sprite_selector.h"
#include <assert.h>
#include <stdio.h>

int main(void) {
    unsigned exhaustive=0u;
    for(unsigned a=0;a<8u;++a)
    for(unsigned b=0;b<8u;++b)
    for(unsigned oy=0;oy<8u;++oy)
    for(unsigned ox=0;ox<8u;++ox) {
        YsPcSpriteSelectorInput in={
            1u,0u,(uint8_t)a,(uint8_t)b,(uint8_t)oy,(uint8_t)ox
        };
        uint8_t raw=0u;
        unsigned index=255u;
        assert(ys_pc_sprite_selector_source(&in,&raw));
        const unsigned expected=0x80u|(((a+oy)&7u)<<3u)|
                                ((b+ox)&7u);
        assert(raw==expected);
        assert(ys_pc_sprite_selector_index(raw,&index));
        assert(index==(expected&63u));
        ++exhaustive;
    }
    assert(exhaustive==4096u);
    unsigned unique=0u;
    for(unsigned i=0;i<64u;++i) {
        YsPcSpriteSelectorInput in={
            1u,0u,(uint8_t)(i>>3u),(uint8_t)(i&7u),0u,0u
        };
        uint8_t raw=0u;unsigned index=255u;
        assert(ys_pc_sprite_selector_source(&in,&raw));
        assert(ys_pc_sprite_selector_index(raw,&index) && index==i);
        ++unique;
    }
    assert(unique==64u);
    YsPcSpriteSelectorInput in={1u,0u,255u,255u,250u,251u};
    uint8_t raw=1u;
    assert(ys_pc_sprite_selector_source(&in,&raw));
    assert(raw==(uint8_t)(0x80u|(((255u+250u)&7u)<<3u)|
                          ((255u+251u)&7u)));
    raw=17u;
    in.c198=0u;
    assert(!ys_pc_sprite_selector_source(&in,&raw) && raw==17u);
    in.c198=1u;in.c011=0x40u;
    assert(!ys_pc_sprite_selector_source(&in,&raw) && raw==17u);
    in.c011=0u;
    assert(!ys_pc_sprite_selector_source(NULL,&raw));
    assert(!ys_pc_sprite_selector_source(&in,NULL));
    unsigned index=1212u;
    assert(!ys_pc_sprite_selector_index(0x7Fu,&index) && index==1212u);
    assert(!ys_pc_sprite_selector_index(0xC0u,&index) && index==1212u);
    /* Original $275C writes $FF, NOT a verified bank6 record index.
       Unchecked Z80 ADD A,A would select entry 127, outside the
       known 64 records. Fail closed instead of aliasing to entry63. */
    assert(!ys_pc_sprite_selector_index(0xFFu,&index) && index==1212u);
    assert(!ys_pc_sprite_selector_index(0x80u,NULL));
    puts("PASS PC-15: 4096 source-derived 8x8 selector equations,"
         " 64 unique original record indices, guards, overflow,"
         " and $FF out-of-range sentinel rejection");
    return 0;
}
