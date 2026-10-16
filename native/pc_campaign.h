#ifndef YS_PC_CAMPAIGN_H
#define YS_PC_CAMPAIGN_H

#include "pc_game.h"

/* Experimental multi-room PROTOTYPE playback. Scene links are canonical
   symbolic IDs, not original Ys bank indices or world-map coordinates. */
typedef struct {
    YsPcContentCatalog catalog;
    YsPcGame game;
    char entry_scene_id[YS_PC_CONTENT_ID_SIZE];
    unsigned completed_scenes;
} YsPcCampaign;

/* Every scene must be traversable and all transitions resolve to a
   finite, acyclic chain. Bad catalog/links leave 'out' unchanged. */
bool ys_pc_campaign_init(YsPcCampaign *out,
                         const YsPcContentCatalog *catalog,
                         const char *entry_scene_id);
/* Build two source-free prototype rooms for manual Alpha-loop rehearsal.
   DOES NOT contain original Ys levels, characters or artwork. */
bool ys_pc_campaign_prototype_catalog(YsPcContentCatalog *out);
/* Execute the normal native PC game tick. Reaching an exit after the
   foe is defeated enters its next linked scene; preserve HP/defeats.
   Final exit ends in CLEAR; START then restarts the entire campaign. */
void ys_pc_campaign_tick(YsPcCampaign *campaign,unsigned buttons);
bool ys_pc_campaign_restart(YsPcCampaign *campaign);
#endif
