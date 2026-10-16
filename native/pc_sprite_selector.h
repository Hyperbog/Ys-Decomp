#ifndef YS_PC_SPRITE_SELECTOR_H
#define YS_PC_SPRITE_SELECTOR_H
#include <stdbool.h>
#include <stdint.h>
#include "pc_sprite_sat.h"

/* Original bank0 $26B6-$26DA is a conditional SOURCE computation,
   not a verified live Ys scene/sprite identity. Byte input names
   are literal original WRAM addresses, not game semantics. */
typedef struct {
    uint8_t c198,c011,c184,c182,c210,c211;
} YsPcSpriteSelectorInput;
/* Success iff $C198 != 0 and bit6 of $C011 is clear.
   The source stores 0x80 | (((C184+C210)&7)<<3)
                          | ((C182+C211)&7) in $C199.
   Returns false (without modifying output) for the skipped path. */
bool ys_pc_sprite_selector_source(const YsPcSpriteSelectorInput *in,
                                  uint8_t *raw_c199);
/* Original bank6 $9932 ADD A,A; LD L,A; LD H,$80
   maps ONLY 0x80..0xBF from this source producer to
   canonical 0..63 directory. Other raw bytes may point outside the
   64 verified entries (e.g. $FF -> 127); reject rather than guess. */
bool ys_pc_sprite_selector_index(uint8_t raw_c199,unsigned *index);
/* SOURCE state -> indexed bank6 SAT composition in native C11.
   Reproduce selection and two-origin original producer, but NOT
   claim state occurs in playable Ys. All outputs preserved on failure. */
bool ys_pc_sprite_stage_source_state(
    const YsPcSpriteRecords *records,const YsPcSpriteSelectorInput *state,
    YsPcSatBuffer *out,uint8_t *raw_c199,unsigned *directory_index);
#endif
