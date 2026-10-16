#include "pc_campaign.h"
#include <string.h>

static bool catalog_valid(const YsPcContentCatalog *cat) {
    if(!cat || !cat->count || cat->count>YS_PC_CONTENT_MAX_SCENES)
        return false;
    for(size_t i=0;i<cat->count;++i) {
        const YsPcSceneContent *s=&cat->scenes[i];
        if(!ys_pc_content_route_ok(s)) return false;
        if(i>0 && strcmp(cat->scenes[i-1u].id,s->id)>=0)
            return false;
        if(s->next_scene_id[0] &&
           !ys_pc_catalog_find(cat,s->next_scene_id))
            return false;
    }
    /* Validate all links, even unreachable optional scenes. */
    for(size_t start=0;start<cat->count;++start) {
        const YsPcSceneContent *p=&cat->scenes[start];
        unsigned hops=0u;
        while(p->next_scene_id[0]) {
            if(++hops>=cat->count) return false; /* cycle */
            p=ys_pc_catalog_find(cat,p->next_scene_id);
            if(!p) return false;
        }
    }
    return true;
}
bool ys_pc_campaign_init(YsPcCampaign *out,
                         const YsPcContentCatalog *cat,
                         const char *entry_id) {
    if(!out || !catalog_valid(cat)) return false;
    const YsPcSceneContent *entry=ys_pc_catalog_find(cat,entry_id);
    if(!entry) return false;
    YsPcCampaign temp={0};
    temp.catalog=*cat;
    memcpy(temp.entry_scene_id,entry->id,YS_PC_CONTENT_ID_SIZE);
    if(!ys_pc_game_reset_named_scene(&temp.game,&temp.catalog,
                                     temp.entry_scene_id))
        return false;
    *out=temp;
    return true;
}
bool ys_pc_campaign_restart(YsPcCampaign *c) {
    if(!c) return false;
    YsPcGame fresh;
    if(!ys_pc_game_reset_named_scene(&fresh,&c->catalog,
                                     c->entry_scene_id))
        return false;
    c->game=fresh;
    c->completed_scenes=0u;
    return true;
}
void ys_pc_campaign_tick(YsPcCampaign *c,unsigned buttons) {
    if(!c) return;
    if(c->game.stage!=YS_PC_TITLE && c->game.stage!=YS_PC_PLAY &&
       (buttons&YS_PC_START)) {
        if(ys_pc_campaign_restart(c)) c->game.stage=YS_PC_PLAY;
        return;
    }
    YsPcStage previous=c->game.stage;
    ys_pc_game_tick(&c->game,buttons);
    if(previous!=YS_PC_PLAY || c->game.stage!=YS_PC_CLEAR ||
       !c->game.scene.next_scene_id[0])
        return;
    YsPcGame next;
    if(!ys_pc_game_reset_named_scene(&next,&c->catalog,
                                     c->game.scene.next_scene_id))
        return; /* Catalog was copied/validated at campaign init. */
    /* HP/defeats never reset across a linked encounter. A later
       scene's initial HP is an upper cap, not a healing station. */
    if(next.hp>c->game.hp) next.hp=c->game.hp;
    next.defeats=c->game.defeats;
    next.frame=c->game.frame;
    next.stage=YS_PC_PLAY;
    c->game=next;
    ++c->completed_scenes;
}
bool ys_pc_campaign_prototype_catalog(YsPcContentCatalog *out) {
    if(!out) return false;
    YsPcContentCatalog cat;
    ys_pc_catalog_init(&cat);
    YsPcSceneContent first;
    ys_pc_content_placeholder(&first);
    memcpy(first.next_scene_id,"prototype.scene.room_two",
           sizeof("prototype.scene.room_two"));
    YsPcSceneContent second;
    ys_pc_content_placeholder(&second);
    memcpy(second.id,"prototype.scene.room_two",
           sizeof("prototype.scene.room_two"));
    second.cells[2][4]=YS_PC_FLOOR;
    second.cells[3][3]=YS_PC_WALL;
    second.foe.x=10u;
    second.foe.y=7u;
    second.foe.hp=2u;
    second.movement_ticks=6u;
    if(ys_pc_catalog_apply(&cat,&first,false)!=YS_PC_CONTENT_OK ||
       ys_pc_catalog_apply(&cat,&second,false)!=YS_PC_CONTENT_OK ||
       !catalog_valid(&cat))
        return false;
    *out=cat;
    return true;
}
