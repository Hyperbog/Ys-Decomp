/* Native PC vertical-slice shell. No Z80, VDP or ROM dependency.
   Test map, character silhouettes and combat values are placeholders. */
#define SDL_MAIN_HANDLED
#include <SDL.h>
#include "pc_game.h"
#include "pc_tiles.h"
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

enum { TILE=32, WIDTH=YS_PC_MAP_W*TILE,
       HEIGHT=(YS_PC_MAP_H+1)*TILE };

static void draw_rect(SDL_Renderer *r,int x,int y,int w,int h,
                      Uint8 red,Uint8 green,Uint8 blue) {
    SDL_Rect box={x,y,w,h};
    SDL_SetRenderDrawColor(r,red,green,blue,255);
    SDL_RenderFillRect(r,&box);
}
static void draw_game(SDL_Renderer *r,const YsPcGame *g,
                      SDL_Texture *atlas,bool show_atlas) {
    SDL_SetRenderDrawColor(r,9,13,25,255);
    SDL_RenderClear(r);
    for(int y=0;y<YS_PC_MAP_H;++y)
        for(int x=0;x<YS_PC_MAP_W;++x) {
            char tile=ys_pc_tile(x,y);
            if(tile=='#') {
                draw_rect(r,x*TILE,y*TILE,TILE,TILE,26,40,64);
                draw_rect(r,x*TILE+2,y*TILE+2,TILE-4,TILE-4,38,58,85);
            } else {
                Uint8 shade=(Uint8)(((x+y)&1)?37:43);
                draw_rect(r,x*TILE,y*TILE,TILE,TILE,shade,49,53);
                if(tile=='G')
                    draw_rect(r,x*TILE+5,y*TILE+4,22,25,
                              g->foe_hp==0?68:92,
                              g->foe_hp==0?205:83,104);
            }
        }
    if(g->stage!=YS_PC_TITLE) {
        if(g->foe_hp>0) {
            draw_rect(r,g->foe_x*TILE+7,g->foe_y*TILE+6,18,20,
                      194,80,82);
            draw_rect(r,g->foe_x*TILE+11,g->foe_y*TILE+3,10,7,
                      228,139,102);
        }
        draw_rect(r,g->x*TILE+6,g->y*TILE+9,20,19,57,133,206);
        draw_rect(r,g->x*TILE+9,g->y*TILE+3,14,12,225,180,114);
    }
    int hud_y=YS_PC_MAP_H*TILE;
    draw_rect(r,0,hud_y,WIDTH,TILE,15,22,35);
    for(int i=0;i<5;++i)
        draw_rect(r,12+i*20,hud_y+9,14,14,
                  i<g->hp?207:55,i<g->hp?73:55,69);
    for(int i=0;i<3;++i)
        draw_rect(r,WIDTH-86+i*22,hud_y+10,14,12,
                  i<g->foe_hp?220:56,i<g->foe_hp?140:56,61);
    if(g->stage==YS_PC_TITLE) {
        draw_rect(r,113,104,WIDTH-226,156,15,25,44);
        draw_rect(r,145,145,WIDTH-290,26,78,142,197);
        draw_rect(r,170,191,WIDTH-340,11,215,172,88);
    } else if(g->stage==YS_PC_CLEAR || g->stage==YS_PC_DEAD) {
        draw_rect(r,130,126,WIDTH-260,103,15,25,44);
        draw_rect(r,152,158,WIDTH-304,26,
                  g->stage==YS_PC_CLEAR?60:180,
                  g->stage==YS_PC_CLEAR?180:60,90);
    }
    if(show_atlas && atlas) {
        /* Historical tile pixels only. Room/map and palette are unknown. */
        draw_rect(r,0,0,WIDTH,YS_PC_MAP_H*TILE,12,17,27);
        SDL_Rect dst={0,16,WIDTH,YS_PC_ATLAS_H*4};
        SDL_RenderCopy(r,atlas,NULL,&dst);
    }
    SDL_RenderPresent(r);
}
static unsigned read_buttons(SDL_GameController *pad) {
    const Uint8 *keys=SDL_GetKeyboardState(NULL);
    unsigned b=0;
    if(keys[SDL_SCANCODE_UP]||keys[SDL_SCANCODE_W]) b|=YS_PC_UP;
    if(keys[SDL_SCANCODE_DOWN]||keys[SDL_SCANCODE_S]) b|=YS_PC_DOWN;
    if(keys[SDL_SCANCODE_LEFT]||keys[SDL_SCANCODE_A]) b|=YS_PC_LEFT;
    if(keys[SDL_SCANCODE_RIGHT]||keys[SDL_SCANCODE_D]) b|=YS_PC_RIGHT;
    if(keys[SDL_SCANCODE_RETURN]||keys[SDL_SCANCODE_SPACE])
        b|=YS_PC_START;
    if(pad && SDL_GameControllerGetAttached(pad)) {
        if(SDL_GameControllerGetButton(pad,SDL_CONTROLLER_BUTTON_DPAD_UP))
            b|=YS_PC_UP;
        if(SDL_GameControllerGetButton(pad,SDL_CONTROLLER_BUTTON_DPAD_DOWN))
            b|=YS_PC_DOWN;
        if(SDL_GameControllerGetButton(pad,SDL_CONTROLLER_BUTTON_DPAD_LEFT))
            b|=YS_PC_LEFT;
        if(SDL_GameControllerGetButton(pad,SDL_CONTROLLER_BUTTON_DPAD_RIGHT))
            b|=YS_PC_RIGHT;
        if(SDL_GameControllerGetButton(pad,SDL_CONTROLLER_BUTTON_START) ||
           SDL_GameControllerGetButton(pad,SDL_CONTROLLER_BUTTON_A))
            b|=YS_PC_START;
    }
    return b;
}
int main(int argc,char **argv) {
    bool smoke=false;
    const char *tile_path=NULL;
    for(int i=1;i<argc;++i) {
        if(strcmp(argv[i],"--smoke")==0 && !smoke) smoke=true;
        else if(strcmp(argv[i],"--tiles")==0 && !tile_path && i+1<argc)
            tile_path=argv[++i];
        else {
            fputs("usage: ys-native-game [--smoke] [--tiles FILE]\n",stderr);
            return EXIT_FAILURE;
        }
    }
    if(SDL_Init(SDL_INIT_VIDEO|SDL_INIT_EVENTS|SDL_INIT_GAMECONTROLLER)!=0) {
        fprintf(stderr,"SDL2 startup: %s\n",SDL_GetError());
        return EXIT_FAILURE;
    }
    SDL_Window *w=SDL_CreateWindow("Ys enhanced PC — placeholder room | Enter: start",
        SDL_WINDOWPOS_CENTERED,SDL_WINDOWPOS_CENTERED,WIDTH*2,HEIGHT*2,
        SDL_WINDOW_SHOWN|SDL_WINDOW_RESIZABLE);
    SDL_Renderer *r=w?SDL_CreateRenderer(w,-1,
        SDL_RENDERER_ACCELERATED|SDL_RENDERER_PRESENTVSYNC):NULL;
    if(w && !r) r=SDL_CreateRenderer(w,-1,SDL_RENDERER_SOFTWARE);
    if(!w || !r || SDL_RenderSetLogicalSize(r,WIDTH,HEIGHT)!=0) {
        fprintf(stderr,"SDL2 display: %s\n",SDL_GetError());
        SDL_DestroyRenderer(r);SDL_DestroyWindow(w);SDL_Quit();
        return EXIT_FAILURE;
    }
    SDL_Texture *atlas=NULL;
    if(tile_path) {
        FILE *fp=fopen(tile_path,"rb");
        YsPcTiles tiles;
        bool valid=fp && ys_pc_tiles_load(fp,&tiles);
        if(fp) fclose(fp);
        if(!valid) {
            fprintf(stderr,"PC-1 invalid derived tile asset: %s\n",tile_path);
            SDL_DestroyRenderer(r);SDL_DestroyWindow(w);SDL_Quit();
            return EXIT_FAILURE;
        }
        uint8_t pixels[YS_PC_ATLAS_W*YS_PC_ATLAS_H*3];
        ys_pc_tiles_grayscale(&tiles,pixels);
        atlas=SDL_CreateTexture(r,SDL_PIXELFORMAT_RGB24,
                                SDL_TEXTUREACCESS_STATIC,
                                YS_PC_ATLAS_W,YS_PC_ATLAS_H);
        if(!atlas || SDL_UpdateTexture(atlas,NULL,pixels,YS_PC_ATLAS_W*3)!=0) {
            fprintf(stderr,"PC-1 SDL texture: %s\n",SDL_GetError());
            SDL_DestroyTexture(atlas);
            SDL_DestroyRenderer(r);SDL_DestroyWindow(w);SDL_Quit();
            return EXIT_FAILURE;
        }
    }
    bool show_atlas=atlas!=NULL; /* F2 switches back to placeholder room. */
    SDL_GameController *pad=NULL;
    for(int i=0;i<SDL_NumJoysticks();++i)
        if(SDL_IsGameController(i)) {
            pad=SDL_GameControllerOpen(i);
            if(pad) break;
        }
    YsPcGame game;
    ys_pc_game_reset(&game);
    bool running=true;
    Uint64 prior=SDL_GetPerformanceCounter();
    const double freq=(double)SDL_GetPerformanceFrequency();
    double accumulator=0;
    while(running) {
        SDL_Event ev;
        while(SDL_PollEvent(&ev)) {
            if(ev.type==SDL_QUIT ||
               (ev.type==SDL_KEYDOWN &&
                ev.key.keysym.sym==SDLK_ESCAPE))
                running=false;
            if(atlas && ev.type==SDL_KEYDOWN && !ev.key.repeat &&
               ev.key.keysym.sym==SDLK_F2)
                show_atlas=!show_atlas;
        }
        Uint64 now=SDL_GetPerformanceCounter();
        double elapsed=(double)(now-prior)/freq;
        prior=now;
        accumulator+=elapsed>0.25?0.25:elapsed;
        unsigned buttons=show_atlas?0u:read_buttons(pad);
        /* Gallery is a read-only reference. Do not move hidden actors. */
        for(int i=0;accumulator>=1.0/60.0 && i<16;++i) {
            ys_pc_game_tick(&game,buttons);
            accumulator-=1.0/60.0;
        }
        char title[160];
        const char *mode=game.stage==YS_PC_TITLE?"Enter: start":
                         game.stage==YS_PC_PLAY?"Move: WASD/arrows | Esc: quit":
                         game.stage==YS_PC_CLEAR?"Room clear! Enter: restart":
                                                  "Defeated! Enter: restart";
        snprintf(title,sizeof(title),
                 "Ys PC prototype (placeholder) | HP %d | enemy %d | %s",
                 game.hp,game.foe_hp,mode);
        if(atlas && show_atlas)
            snprintf(title,sizeof(title),
                     "Ys bank-3 source tiles (176) | grayscale PREVIEW | F2: room");
        else if(atlas)
            snprintf(title,sizeof(title),
                     "Ys PC placeholder room | F2: authentic bank-3 tile gallery");
        SDL_SetWindowTitle(w,title);
        draw_game(r,&game,atlas,show_atlas);
        if(smoke && game.frame>=12u) running=false;
        SDL_Delay(1);
    }
    if(pad) SDL_GameControllerClose(pad);
    SDL_DestroyTexture(atlas);
    SDL_DestroyRenderer(r);SDL_DestroyWindow(w);SDL_Quit();
    return EXIT_SUCCESS;
}
