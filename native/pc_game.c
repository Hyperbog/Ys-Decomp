#include "pc_game.h"
#include <stddef.h>

/* A placeholder test room, not a recovered map from the SMS cartridge. */
static const char *const room[YS_PC_MAP_H]={
    "################",
    "#..............#",
    "#...####.......#",
    "#..............#",
    "#......###.....#",
    "#..............#",
    "#..###.........#",
    "#..............#",
    "#........##....#",
    "#..............#",
    "#............G.#",
    "################"
};

char ys_pc_tile(int x,int y) {
    if(x<0 || x>=YS_PC_MAP_W || y<0 || y>=YS_PC_MAP_H)
        return '#';
    return room[y][x];
}
void ys_pc_game_reset(YsPcGame *g) {
    if(!g) return;
    *g=(YsPcGame){0};
    g->stage=YS_PC_TITLE;
    g->x=2;g->y=2;
    g->foe_x=9;g->foe_y=7;
    g->hp=5;g->foe_hp=3;
}
void ys_pc_game_tick(YsPcGame *g,unsigned buttons) {
    if(!g) return;
    ++g->frame;
    if(g->stage!=YS_PC_PLAY) {
        if(buttons&YS_PC_START) {
            ys_pc_game_reset(g);
            g->stage=YS_PC_PLAY;
        }
        return;
    }
    if(g->move_delay) {
        --g->move_delay;
        return;
    }
    int dx=0,dy=0;
    if(buttons&YS_PC_UP) dy=-1;
    else if(buttons&YS_PC_DOWN) dy=1;
    else if(buttons&YS_PC_LEFT) dx=-1;
    else if(buttons&YS_PC_RIGHT) dx=1;
    if(!dx && !dy) return;
    g->move_delay=7u; /* Deterministic eight-tick movement interval. */
    int nx=g->x+dx,ny=g->y+dy;
    char tile=ys_pc_tile(nx,ny);
    if(tile=='#' || (tile=='G' && g->foe_hp>0)) return;
    if(nx==g->foe_x && ny==g->foe_y && g->foe_hp>0) {
        /* A provisional bump-combat interaction, not original balance. */
        --g->foe_hp;
        if(!g->foe_hp) ++g->defeats;
        else if(--g->hp==0) g->stage=YS_PC_DEAD;
        return;
    }
    g->x=nx;g->y=ny;
    if(tile=='G') g->stage=YS_PC_CLEAR;
}
