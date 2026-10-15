#include "pc_campaign.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

/* ROM-free replay of a COMPLETE but explicitly PROTOTYPE 2-room loop.
   No source Ys map, movement physics, actor or palette is claimed. */
static void move_one(YsPcCampaign *c,int x,int y) {
    YsPcGame *g=&c->game;
    unsigned key=0u;
    if(x==g->x+1 && y==g->y) key=YS_PC_RIGHT;
    else if(x==g->x-1 && y==g->y) key=YS_PC_LEFT;
    else if(x==g->x && y==g->y+1) key=YS_PC_DOWN;
    else if(x==g->x && y==g->y-1) key=YS_PC_UP;
    assert(key && g->stage==YS_PC_PLAY);
    unsigned start_completed=c->completed_scenes;
    for(unsigned k=0;k<8u;++k) {
        while(g->move_delay) ys_pc_campaign_tick(c,0u);
        ys_pc_campaign_tick(c,key);
        if(g->stage==YS_PC_CLEAR || g->stage==YS_PC_DEAD ||
           c->completed_scenes!=start_completed ||
           (g->x==x && g->y==y)) return;
    }
    assert(0 && "prototype move loop failed");
}
static void walk_to(YsPcCampaign *c,unsigned goal_x,unsigned goal_y) {
    const YsPcGame *g=&c->game;
    assert(g->stage==YS_PC_PLAY && goal_x<YS_PC_MAP_W &&
           goal_y<YS_PC_MAP_H);
    enum { COUNT=YS_PC_MAP_W*YS_PC_MAP_H };
    int previous[COUNT];
    for(unsigned i=0;i<COUNT;++i) previous[i]=-1;
    int queue[COUNT];
    unsigned front=0u,back=0u;
    int start=g->y*YS_PC_MAP_W+g->x;
    int finish=(int)(goal_y*YS_PC_MAP_W+goal_x);
    previous[start]=start;
    queue[back++]=start;
    static const int dx[4]={-1,1,0,0},dy[4]={0,0,-1,1};
    while(front<back && previous[finish]<0) {
        int current=queue[front++];
        int x=current%YS_PC_MAP_W,y=current/YS_PC_MAP_W;
        for(unsigned d=0;d<4u;++d) {
            int xx=x+dx[d],yy=y+dy[d];
            if(xx<0||yy<0||xx>=YS_PC_MAP_W||yy>=YS_PC_MAP_H)
                continue;
            int next=yy*YS_PC_MAP_W+xx;
            char t=ys_pc_game_tile(g,xx,yy);
            if(previous[next]>=0 || t=='#' ||
               (t=='G' && g->foe_hp>0)) continue;
            previous[next]=current;
            queue[back++]=next;
        }
    }
    assert(previous[finish]>=0);
    int route[COUNT];
    unsigned n=0u;
    for(int at=finish;at!=start;at=previous[at])
        route[n++]=at;
    unsigned origin=c->completed_scenes;
    while(n) {
        int at=route[--n];
        move_one(c,at%YS_PC_MAP_W,at/YS_PC_MAP_W);
        if(c->completed_scenes!=origin ||
           c->game.stage!=YS_PC_PLAY) return;
    }
    assert(c->game.x==(int)goal_x && c->game.y==(int)goal_y);
}
static void test_full_prototype(void) {
    YsPcContentCatalog catalog;
    assert(ys_pc_campaign_prototype_catalog(&catalog));
    assert(catalog.count==2u);
    YsPcCampaign c;
    assert(ys_pc_campaign_init(&c,&catalog,"prototype.scene.test_room"));
    assert(c.game.stage==YS_PC_TITLE && c.game.hp==5 &&
           c.completed_scenes==0u);
    ys_pc_campaign_tick(&c,YS_PC_START);
    assert(c.game.stage==YS_PC_PLAY);
    walk_to(&c,9u,7u);
    assert(c.game.defeats==1 && c.game.foe_hp==0 && c.game.hp==3);
    walk_to(&c,13u,10u);
    assert(c.completed_scenes==1u &&
           strcmp(c.game.scene.id,"prototype.scene.room_two")==0 &&
           c.game.stage==YS_PC_PLAY && c.game.hp==3 &&
           c.game.foe_hp==2 && c.game.defeats==1 &&
           c.game.scene.movement_ticks==6u);
    walk_to(&c,10u,7u);
    assert(c.game.defeats==2 && c.game.hp==2 &&
           c.game.foe_hp==0);
    walk_to(&c,13u,10u);
    assert(c.game.stage==YS_PC_CLEAR && c.completed_scenes==1u &&
           c.game.defeats==2 && c.game.hp==2);
    ys_pc_campaign_tick(&c,YS_PC_START);
    assert(c.game.stage==YS_PC_PLAY &&
           c.completed_scenes==0u && c.game.hp==5 &&
           c.game.defeats==0 &&
           strcmp(c.game.scene.id,"prototype.scene.test_room")==0);

    /* Restarts restore initial content; previous catalog changes
       cannot mutate the owned campaign after creation. */
    catalog.scenes[0].cells[2][4]='?';
    assert(ys_pc_content_route_ok(&c.game.scene));
    assert(c.game.scene.cells[2][4]=='#');
    assert(ys_pc_campaign_restart(&c));
    assert(c.game.stage==YS_PC_TITLE && c.completed_scenes==0u);
}
static void test_bad_links(void) {
    YsPcContentCatalog catalog;
    assert(ys_pc_campaign_prototype_catalog(&catalog));
    YsPcCampaign sentinel;
    memset(&sentinel,0xA5,sizeof(sentinel));
    YsPcCampaign prior=sentinel;
    assert(!ys_pc_campaign_init(NULL,&catalog,"prototype.scene.test_room"));
    assert(!ys_pc_campaign_init(&sentinel,NULL,"prototype.scene.test_room"));
    assert(!ys_pc_campaign_init(&sentinel,&catalog,"not.a.scene"));
    assert(!ys_pc_campaign_init(&sentinel,&catalog,NULL));
    assert(memcmp(&sentinel,&prior,sizeof(sentinel))==0);
    /* Both of these prototype rooms are independently navigable. */
    for(size_t i=0;i<catalog.count;++i)
        assert(ys_pc_content_route_ok(&catalog.scenes[i]));

    YsPcContentCatalog broken=catalog;
    const YsPcSceneContent *first=ys_pc_catalog_find(
        &broken,"prototype.scene.test_room");
    assert(first);
    /* Sorted order is room_two, then test_room. */
    YsPcSceneContent *start=&broken.scenes[1];
    assert(strcmp(start->id,"prototype.scene.test_room")==0);
    memcpy(start->next_scene_id,"prototype.scene.missing",
           sizeof("prototype.scene.missing"));
    assert(!ys_pc_campaign_init(&sentinel,&broken,start->id));
    assert(memcmp(&sentinel,&prior,sizeof(sentinel))==0);
    broken=catalog;
    memcpy(broken.scenes[0].next_scene_id,"prototype.scene.test_room",
           sizeof("prototype.scene.test_room"));
    assert(!ys_pc_campaign_init(&sentinel,&broken,start->id));
    broken=catalog;
    YsPcSceneContent invalid=broken.scenes[1];
    memcpy(invalid.next_scene_id,invalid.id,sizeof(invalid.id));
    assert(ys_pc_content_validate(&invalid)==YS_PC_CONTENT_BAD_LINK);
    memcpy(invalid.next_scene_id,"../invalid",sizeof("../invalid"));
    assert(ys_pc_content_validate(&invalid)==YS_PC_CONTENT_BAD_LINK);

    broken=catalog;
    /* Box in the original goal. All cells still have legal types,
       but there is no path to the required exit. */
    broken.scenes[1].cells[10][12]='#';
    broken.scenes[1].cells[9][13]='#';
    broken.scenes[1].cells[10][14]='#';
    assert(ys_pc_content_validate(&broken.scenes[1])==YS_PC_CONTENT_OK);
    assert(!ys_pc_content_route_ok(&broken.scenes[1]));
    assert(!ys_pc_campaign_init(&sentinel,&broken,start->id));
    assert(memcmp(&sentinel,&prior,sizeof(sentinel))==0);
    broken=catalog;
    YsPcSceneContent temp=broken.scenes[0];
    broken.scenes[0]=broken.scenes[1];
    broken.scenes[1]=temp;
    assert(!ys_pc_campaign_init(&sentinel,&broken,"prototype.scene.test_room"));
    assert(memcmp(&sentinel,&prior,sizeof(sentinel))==0);
}
static void test_single_scene_compatibility(void) {
    YsPcContentCatalog only;
    ys_pc_catalog_init(&only);
    YsPcSceneContent base;
    ys_pc_content_placeholder(&base);
    assert(ys_pc_catalog_apply(&only,&base,false)==YS_PC_CONTENT_OK);
    YsPcCampaign c;
    assert(ys_pc_campaign_init(&c,&only,base.id));
    assert(c.catalog.count==1u);
    ys_pc_campaign_tick(&c,YS_PC_START);
    assert(c.game.stage==YS_PC_PLAY);
    walk_to(&c,9u,7u);
    walk_to(&c,13u,10u);
    assert(c.game.stage==YS_PC_CLEAR && c.completed_scenes==0u);
}
int main(void) {
    test_full_prototype();
    test_bad_links();
    test_single_scene_compatibility();
    puts("PASS PC-13: two-room ROM-free native prototype walkthrough,"
         " persistent HP/defeats, restart, deterministic content-link guards"
         " and unchanged one-room final exit");
    return 0;
}
