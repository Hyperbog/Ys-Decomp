#ifndef YS_PC_SCENES_H
#define YS_PC_SCENES_H
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>

enum {
    YS_PC_SCENE_DISPATCH_COUNT=9,
    YS_PC_BANK1_SCENE_ENTRY_COUNT=8,
    YS_PC_SCENE_FILE_BYTES=16+2*(9+8)
};
typedef struct {
    uint16_t fixed_handlers[YS_PC_SCENE_DISPATCH_COUNT];
    uint16_t bank1_entries[YS_PC_BANK1_SCENE_ENTRY_COUNT];
} YsPcSceneDirectory;
typedef struct {
    uint8_t c119, c181, c181_high_bit;
    uint16_t scene_handler; /* Source handler selected by C119. */
    unsigned object_group;  /* Index of C181 & 0x7F; only valid if has_group. */
    bool has_group;
} YsPcSceneSelection;

/* Two independent source selectors, not a known scene-to-map mapping.
   Caller supplies WRAM snapshot values; no active runtime state inferred. */
bool ys_pc_scenes_load(FILE *file,YsPcSceneDirectory *out);
bool ys_pc_scene_select(const YsPcSceneDirectory *source,
                        uint8_t c119,uint8_t c181,YsPcSceneSelection *out);
#endif
