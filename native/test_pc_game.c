#include "pc_game.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static void test_map_and_title(void) {
    YsPcGame g;
    ys_pc_game_reset(&g);
    assert(g.stage==YS_PC_TITLE && g.x==2 && g.y==2 && g.hp==5);
    assert(ys_pc_tile(-1,0)=='#' && ys_pc_tile(16,0)=='#');
    assert(ys_pc_tile(13,10)=='G' && ys_pc_tile(4,2)=='#');
    for(int y=0;y<YS_PC_MAP_H;++y) {
        int len=0;
        while(ys_pc_tile(len,y)!='#' && len<YS_PC_MAP_W) ++len;
        /* All map row ends must be blocked, regardless of interior tiles. */
        assert(ys_pc_tile(0,y)=='#' &&
               ys_pc_tile(YS_PC_MAP_W-1,y)=='#');
    }
    ys_pc_game_tick(&g,YS_PC_RIGHT);
    assert(g.stage==YS_PC_TITLE && g.x==2);
    ys_pc_game_tick(&g,YS_PC_START);
    assert(g.stage==YS_PC_PLAY && g.frame==0u);
}
static void test_wall_repeat_and_controls(void) {
    YsPcGame g;
    ys_pc_game_reset(&g);
    ys_pc_game_tick(&g,YS_PC_START);
    g.x=1;g.y=1;
    ys_pc_game_tick(&g,YS_PC_LEFT);
    assert(g.x==1 && g.move_delay==7u);
    for(int i=0;i<7;++i) ys_pc_game_tick(&g,YS_PC_RIGHT);
    assert(g.x==1 && g.move_delay==0u);
    ys_pc_game_tick(&g,YS_PC_RIGHT);
    assert(g.x==2 && g.y==1);
    g.x=3;g.y=2;g.move_delay=0;
    ys_pc_game_tick(&g,YS_PC_RIGHT);
    assert(g.x==3 && g.y==2);
}
static void test_bump_combat_and_goal(void) {
    YsPcGame g;
    ys_pc_game_reset(&g);
    ys_pc_game_tick(&g,YS_PC_START);
    g.x=8;g.y=7;
    for(int hit=0;hit<3;++hit) {
        ys_pc_game_tick(&g,YS_PC_RIGHT);
        assert(g.x==8 && g.y==7 && g.foe_hp==2-hit);
        if(hit<2)
            for(int frame=0;frame<7;++frame)
                ys_pc_game_tick(&g,YS_PC_RIGHT);
    }
    assert(g.defeats==1 && g.hp==3);
    g.x=12;g.y=10;g.move_delay=0u;
    ys_pc_game_tick(&g,YS_PC_RIGHT);
    assert(g.stage==YS_PC_CLEAR && g.x==13 && g.y==10);
    ys_pc_game_tick(&g,YS_PC_START);
    assert(g.stage==YS_PC_PLAY && g.foe_hp==3 &&
           g.defeats==0 && g.hp==5 && g.x==2);
}
static void test_locked_goal_and_defeat(void) {
    YsPcGame g;
    ys_pc_game_reset(&g);
    ys_pc_game_tick(&g,YS_PC_START);
    g.x=12;g.y=10;
    ys_pc_game_tick(&g,YS_PC_RIGHT);
    assert(g.stage==YS_PC_PLAY && g.x==12);
    g.x=8;g.y=7;g.hp=1;g.move_delay=0;
    ys_pc_game_tick(&g,YS_PC_RIGHT);
    assert(g.stage==YS_PC_DEAD && g.hp==0 && g.foe_hp==2);
}
int main(void) {
    test_map_and_title();
    test_wall_repeat_and_controls();
    test_bump_combat_and_goal();
    test_locked_goal_and_defeat();
    puts("PASS native PC placeholder room: title, collisions, repeat, combat, goal and reset");
    return 0;
}
