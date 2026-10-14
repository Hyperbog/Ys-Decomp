#include "pc_content.h"
#include "pc_game.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static void copy_id(char *dest,const char *src) {
    size_t len=strlen(src);
    assert(len<YS_PC_CONTENT_ID_SIZE);
    memset(dest,0,YS_PC_CONTENT_ID_SIZE);
    memcpy(dest,src,len);
}
static void expect_failed_update(YsPcContentCatalog *catalog,
                                 YsPcSceneContent *scene,
                                 YsPcContentStatus expected) {
    YsPcContentCatalog before=*catalog;
    assert(ys_pc_catalog_apply(catalog,scene,false)==expected);
    assert(memcmp(catalog,&before,sizeof(before))==0);
}
static void test_vanilla(void) {
    YsPcSceneContent scene;
    ys_pc_content_placeholder(&scene);
    assert(scene.schema_version==1u);
    assert(strcmp(scene.id,"prototype.scene.test_room")==0);
    assert(strcmp(scene.player.id,"prototype.actor.player")==0);
    assert(strcmp(scene.foe.id,"prototype.actor.foe")==0);
    assert(ys_pc_content_validate(&scene)==YS_PC_CONTENT_OK);
    assert(scene.movement_ticks==8u && scene.player.hp==5u &&
           scene.foe.hp==3u && scene.player.x==2u &&
           scene.foe.x==9u && scene.foe.y==7u);
    for(int y=0;y<YS_PC_MAP_H;++y)
        for(int x=0;x<YS_PC_MAP_W;++x)
            assert(ys_pc_content_cell(&scene,x,y)==ys_pc_tile(x,y));
    assert(ys_pc_content_cell(&scene,-1,0)=='#');
    YsPcGame vanilla,canonical;
    ys_pc_game_reset(&vanilla);
    assert(ys_pc_game_reset_scene(&canonical,&scene));
    assert(vanilla.stage==canonical.stage && vanilla.hp==canonical.hp &&
           vanilla.foe_hp==canonical.foe_hp &&
           vanilla.x==canonical.x && vanilla.y==canonical.y);
    const unsigned inputs[]={YS_PC_START,YS_PC_LEFT,YS_PC_RIGHT,
                             YS_PC_DOWN,YS_PC_RIGHT,YS_PC_RIGHT,
                             YS_PC_RIGHT,0u,YS_PC_RIGHT,0u};
    for(unsigned i=0;i<sizeof(inputs)/sizeof(inputs[0]);++i) {
        ys_pc_game_tick(&vanilla,inputs[i]);
        ys_pc_game_tick(&canonical,inputs[i]);
        assert(memcmp(&vanilla,&canonical,sizeof(vanilla))==0);
    }
    assert(ys_pc_game_tile(NULL,0,0)=='#');
    assert(ys_pc_game_tile(&canonical,-1,0)=='#');
}
static void test_validation(void) {
    YsPcSceneContent s;ys_pc_content_placeholder(&s);
    assert(ys_pc_content_validate(NULL)==YS_PC_CONTENT_INVALID);
    s.schema_version=2u;assert(ys_pc_content_validate(&s)==YS_PC_CONTENT_VERSION);
    s.schema_version=1u;
    copy_id(s.id,"wrong");assert(ys_pc_content_validate(&s)==YS_PC_CONTENT_BAD_ID);
    copy_id(s.id,"evil/../route");assert(ys_pc_content_validate(&s)==YS_PC_CONTENT_BAD_ID);
    copy_id(s.id,"prototype.scene.test_room");
    memset(s.id,'a',sizeof(s.id));assert(ys_pc_content_validate(&s)==YS_PC_CONTENT_BAD_ID);
    copy_id(s.id,"prototype.scene.test_room");
    copy_id(s.foe.id,s.player.id);
    assert(ys_pc_content_validate(&s)==YS_PC_CONTENT_BAD_ID);
    copy_id(s.foe.id,"prototype.actor.foe");
    s.cells[2][4]='?';assert(ys_pc_content_validate(&s)==YS_PC_CONTENT_BAD_TILE);
    s.cells[2][4]='#';
    s.cells[0][1]='.';assert(ys_pc_content_validate(&s)==YS_PC_CONTENT_BAD_TILE);
    s.cells[0][1]='#';
    s.cells[10][13]='.';
    assert(ys_pc_content_validate(&s)==YS_PC_CONTENT_BAD_SPAWN);
    s.cells[10][13]='G';
    s.player.x=0u;
    assert(ys_pc_content_validate(&s)==YS_PC_CONTENT_BAD_SPAWN);
    s.player.x=2u;
    s.player.hp=0u;assert(ys_pc_content_validate(&s)==YS_PC_CONTENT_BAD_SPAWN);
    s.player.hp=5u;
    s.movement_ticks=0u;
    assert(ys_pc_content_validate(&s)==YS_PC_CONTENT_BAD_SPAWN);
    s.movement_ticks=8u;
    assert(ys_pc_content_validate(&s)==YS_PC_CONTENT_OK);
}
static void test_catalog(void) {
    YsPcContentCatalog a,b;
    ys_pc_catalog_init(&a);ys_pc_catalog_init(&b);
    YsPcSceneContent base,second;
    ys_pc_content_placeholder(&base);second=base;
    copy_id(second.id,"example.scene.alternate");
    copy_id(second.player.id,"example.actor.player");
    copy_id(second.foe.id,"example.actor.foe");
    second.cells[2][4]='.';
    second.movement_ticks=3u;
    second.player.hp=7u;
    second.foe.hp=2u;
    assert(ys_pc_content_validate(&second)==YS_PC_CONTENT_OK);
    assert(ys_pc_catalog_apply(&a,&base,false)==YS_PC_CONTENT_OK);
    assert(ys_pc_catalog_apply(&a,&second,false)==YS_PC_CONTENT_OK);
    assert(ys_pc_catalog_apply(&b,&second,false)==YS_PC_CONTENT_OK);
    assert(ys_pc_catalog_apply(&b,&base,false)==YS_PC_CONTENT_OK);
    /* Sorted IDs and content are independent of add order. */
    assert(memcmp(&a,&b,sizeof(a))==0);
    assert(a.count==2u &&
           strcmp(a.scenes[0].id,"example.scene.alternate")==0);
    assert(ys_pc_catalog_find(&a,"example.scene.alternate")!=NULL);
    assert(ys_pc_catalog_find(&a,"prototype.scene.test_room")!=NULL);
    assert(ys_pc_catalog_find(&a,"example.scene.missing")==NULL);
    assert(ys_pc_catalog_find(NULL,base.id)==NULL);
    expect_failed_update(&a,&base,YS_PC_CONTENT_CONFLICT);
    YsPcSceneContent missing=base;
    copy_id(missing.id,"other.scene.unknown");
    assert(ys_pc_catalog_apply(&a,&missing,true)==YS_PC_CONTENT_NOT_FOUND);
    assert(a.count==2u);
    YsPcSceneContent changed=second;
    changed.cells[2][5]='.'; /* baseline is blocked at this position */
    assert(ys_pc_catalog_apply(&a,&changed,true)==YS_PC_CONTENT_OK);
    assert(ys_pc_catalog_find(&a,changed.id)->cells[2][5]=='.');
    assert(ys_pc_catalog_find(&a,base.id)->cells[2][5]=='#');
    assert(ys_pc_catalog_apply(NULL,&base,false)==YS_PC_CONTENT_INVALID);
    changed.cells[2][5]='?';
    expect_failed_update(&a,&changed,YS_PC_CONTENT_BAD_TILE);
    YsPcContentCatalog full={0};
    for(unsigned i=0;i<YS_PC_CONTENT_MAX_SCENES;++i) {
        char id[64];snprintf(id,sizeof(id),"test.scene.%u",i);
        YsPcSceneContent item=base;
        copy_id(item.id,id);
        assert(ys_pc_catalog_apply(&full,&item,false)==YS_PC_CONTENT_OK);
    }
    YsPcSceneContent extra=base;
    assert(ys_pc_catalog_apply(&full,&extra,false)==YS_PC_CONTENT_FULL);
}
static void test_content_driven_gameplay(void) {
    YsPcSceneContent customized;
    ys_pc_content_placeholder(&customized);
    copy_id(customized.id,"example.scene.alternate");
    customized.cells[2][4]='.';
    customized.movement_ticks=3u;
    customized.player.hp=7u;
    customized.foe.hp=2u;
    YsPcGame g;ys_pc_game_reset(&g);
    assert(ys_pc_game_reset_scene(&g,&customized));
    assert(g.hp==7 && g.foe_hp==2 && g.x==2 && g.y==2);
    assert(ys_pc_game_tile(&g,4,2)=='.');
    ys_pc_game_tick(&g,YS_PC_START);
    g.x=3;g.y=2;
    ys_pc_game_tick(&g,YS_PC_RIGHT);
    assert(g.x==4 && g.y==2 && g.move_delay==2u);
    ys_pc_game_tick(&g,YS_PC_RIGHT);
    ys_pc_game_tick(&g,YS_PC_RIGHT);
    assert(g.x==4 && g.move_delay==0u);
    YsPcGame before=g;
    YsPcSceneContent bad=customized;bad.cells[4][0]='.';
    assert(!ys_pc_game_reset_scene(&g,&bad));
    assert(memcmp(&g,&before,sizeof(g))==0);
    g.stage=YS_PC_CLEAR;ys_pc_game_tick(&g,YS_PC_START);
    assert(g.stage==YS_PC_PLAY && g.hp==7 && g.foe_hp==2 &&
           g.x==2 && g.y==2 && g.scene.movement_ticks==3);
}
int main(void) {
    test_vanilla();test_validation();
    test_catalog();test_content_driven_gameplay();
    puts("PASS PC-10: default game parity, symbolic ID registry,"
         " deterministic add/replace, rejection, scene-driven gameplay");
    return 0;
}
