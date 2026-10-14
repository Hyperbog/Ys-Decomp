#include "pc_game.h"

char ys_pc_tile(int x,int y) {
    YsPcSceneContent prototype;
    ys_pc_content_placeholder(&prototype);
    return ys_pc_content_cell(&prototype,x,y);
}
char ys_pc_game_tile(const YsPcGame *g,int x,int y) {
    return g?ys_pc_content_cell(&g->scene,x,y):'#';
}
bool ys_pc_game_reset_scene(YsPcGame *g,const YsPcSceneContent *s) {
    if(!g || ys_pc_content_validate(s)!=YS_PC_CONTENT_OK)
        return false;
    YsPcGame next={0};
    next.scene=*s; /* copy before mutating g: caller may pass &g->scene */
    next.stage=YS_PC_TITLE;
    next.x=s->player.x;next.y=s->player.y;
    next.foe_x=s->foe.x;next.foe_y=s->foe.y;
    next.hp=s->player.hp;next.foe_hp=s->foe.hp;
    *g=next;
    return true;
}
void ys_pc_game_reset(YsPcGame *g) {
    if(!g) return;
    YsPcSceneContent prototype;
    ys_pc_content_placeholder(&prototype);
    (void)ys_pc_game_reset_scene(g,&prototype);
}
void ys_pc_game_tick(YsPcGame *g,unsigned buttons) {
    if(!g) return;
    ++g->frame;
    if(g->stage!=YS_PC_PLAY) {
        if(buttons&YS_PC_START) {
            (void)ys_pc_game_reset_scene(g,&g->scene);
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
    g->move_delay=(unsigned)(g->scene.movement_ticks-1u);
    int nx=g->x+dx,ny=g->y+dy;
    char tile=ys_pc_game_tile(g,nx,ny);
    if(tile=='#' || (tile=='G' && g->foe_hp>0)) return;
    if(nx==g->foe_x && ny==g->foe_y && g->foe_hp>0) {
        /* Provisional PC-0 bump combat; NOT source-verified Ys AI. */
        --g->foe_hp;
        if(!g->foe_hp) ++g->defeats;
        else if(--g->hp==0) g->stage=YS_PC_DEAD;
        return;
    }
    g->x=nx;g->y=ny;
    if(tile=='G') g->stage=YS_PC_CLEAR;
}
