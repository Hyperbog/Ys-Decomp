/* Native PC vertical-slice shell. No Z80, VDP or ROM dependency.
   Test map, character silhouettes and combat values are placeholders. */
#define SDL_MAIN_HANDLED
#include <SDL.h>
#include "pc_game.h"
#include "pc_tiles.h"
#include "pc_records.h"
#include "pc_objects.h"
#include "pc_scenes.h"
#include "pc_nametable.h"
#include "pc_patterns.h"
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
                      SDL_Texture *atlas,bool show_atlas,
                      const YsPcRecords *records,bool show_records,
                      unsigned group,bool show_projection,
                      const YsPcObjectTypes *types,
                      const YsPcSceneDirectory *scenes,bool show_scenes,
                      unsigned scene_idx,unsigned bank1_idx,
                      const YsPcNameTable *name_table,bool show_name_table,
                      SDL_Texture *pattern_preview,bool show_pattern_preview) {
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
    if(show_records && records && group<YS_PC_GROUP_COUNT) {
        /* Each COLUMN is a four-byte source record; ROWS are unknown fields.
           This is a numeric source-data visualization, NOT map geometry. */
        draw_rect(r,0,0,WIDTH,YS_PC_MAP_H*TILE,12,17,27);
        if(show_projection) {
            /* Two scaled object work fields, NOT a recovered world map.
               Both axes are normalized diagnostic register values. */
            YsPcObjectProjection projection;
            if(types ? ys_pc_project_objects_typed(records,group,types,&projection)
                     : ys_pc_project_objects(records,group,&projection)) {
                for(unsigned k=0;k<=4u;++k) {
                    int gx=8+(int)k*(WIDTH-16)/4;
                    int gy=12+(int)k*(YS_PC_MAP_H*TILE-24)/4;
                    draw_rect(r,gx,12,1,YS_PC_MAP_H*TILE-24,38,55,75);
                    draw_rect(r,8,gy,WIDTH-16,1,38,55,75);
                }
                for(unsigned i=0;i<projection.count;++i) {
                    const YsPcObjectSlot *slot=&projection.objects[i];
                    int px=8+(int)((unsigned)slot->value_a*
                                   (WIDTH-22u)/2048u);
                    int py=12+(int)((unsigned)slot->value_b*
                                    (YS_PC_MAP_H*TILE-30u)/2048u);
                    draw_rect(r,px-3,py-3,9,9,40,46,66);
                    if(types && (slot->source[1]&0x80u))
                        draw_rect(r,px-1,py-1,5,5,104,204,173);
                    else
                        draw_rect(r,px-1,py-1,5,5,205,172,106);
                }
            }
        } else {
        unsigned offset=ys_pc_records_start(records,group);
        unsigned count=records->groups[group].count;
        for(unsigned i=0;i<count;++i)
            for(unsigned field=0;field<YS_PC_RECORD_WIDTH;++field) {
                uint8_t raw=records->records[offset+i][field];
                int height=2+(int)raw*48/255;
                int x=8+(int)i*31,top=22+(int)field*88;
                Uint8 red=(field==0u)?159u:55u;
                Uint8 green=(field==1u)?183u:80u;
                Uint8 blue=(field==2u)?197u:96u;
                if(field==3u) { red=203u;green=145u;blue=69u; }
                draw_rect(r,x,top,24,55,29,42,58);
                draw_rect(r,x,top+55-height,24,height,red,green,blue);
            }
        /* 16 transferred source bytes: their color meaning is unknown. */
        for(unsigned i=0;i<YS_PC_STAGING_BYTES;++i) {
            uint8_t raw=records->staging[i];
            int h=2+(int)raw*15/255;
            draw_rect(r,8+(int)i*31,YS_PC_MAP_H*TILE-18,
                      22,16,39,49,68);
            draw_rect(r,8+(int)i*31,YS_PC_MAP_H*TILE-2-h,
                      22,h,129,153,168);
        }
        }
    }
    if(show_scenes && scenes) {
        /* Distinct original dispatch tables. NOT a recovered map.
           These are pointer-value bars, not actor placements. */
        draw_rect(r,0,0,WIDTH,YS_PC_MAP_H*TILE,12,17,27);
        for(unsigned i=0;i<YS_PC_SCENE_DISPATCH_COUNT;++i) {
            int x=13+(int)i*55;
            int height=35+(int)((unsigned)(scenes->fixed_handlers[i]-0x2C36u)*95u/0x1000u);
            draw_rect(r,x,174-height,43,height,
                      i==scene_idx?204:72,i==scene_idx?160:115,105);
        }
        for(unsigned i=0;i<YS_PC_BANK1_SCENE_ENTRY_COUNT;++i) {
            int x=20+(int)i*61;
            int height=24+(int)((unsigned)(scenes->bank1_entries[i]-0x4C13u)*80u/0x60u);
            draw_rect(r,x,334-height,42,height,
                      i==bank1_idx?113:65,i==bank1_idx?183:105,175);
        }
    }
    if(show_name_table && name_table) {
        /* Source-authentic M43 name entries at VRAM $3900-$3EFF.
           Diagnostic INDEX grayscale, NOT actual Ys colors or a game map.
           The unknown upper 4 name-table rows $3800-$38FF are omitted. */
        draw_rect(r,0,0,WIDTH,YS_PC_MAP_H*TILE,12,17,27);
        for(unsigned y=0;y<YS_PC_NT_H;++y)
            for(unsigned x=0;x<YS_PC_NT_W;++x) {
                YsPcNameCell cell;
                if(!ys_pc_nametable_cell(name_table,x,y,&cell))
                    continue;
                Uint8 shade=(Uint8)(26u+
                    ((unsigned)cell.pattern*185u)/511u);
                int px=(int)x*16,py=12+(int)y*15;
                draw_rect(r,px,py,15,14,shade,shade,shade);
                if(cell.palette_1)
                    draw_rect(r,px+1,py+11,13,2,125,125,125);
                if(cell.priority)
                    draw_rect(r,px+1,py+1,13,2,241,241,241);
            }
    }
    if(show_pattern_preview && pattern_preview) {
        /* Source-derived pattern/name-table composition in index-gray.
           Tile indices 384..511 are magenta UNRESOLVED. No CRAM palette. */
        draw_rect(r,0,0,WIDTH,YS_PC_MAP_H*TILE,12,17,27);
        SDL_Rect destination={0,0,WIDTH,YS_PC_MAP_H*TILE};
        SDL_RenderCopy(r,pattern_preview,NULL,&destination);
        /* Hide prototype health/enemy bars below source diagnostics. */
        draw_rect(r,0,YS_PC_MAP_H*TILE,WIDTH,TILE,15,22,35);
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
    bool smoke_projection=false;
    const char *tile_path=NULL;
    const char *record_path=NULL;
    const char *object_types_path=NULL;
    const char *scene_path=NULL;
    const char *name_table_path=NULL;
    const char *pattern_path=NULL;
    for(int i=1;i<argc;++i) {
        if(strcmp(argv[i],"--smoke")==0 && !smoke) smoke=true;
        else if(strcmp(argv[i],"--smoke-projection")==0 &&
                !smoke_projection) smoke_projection=true;
        else if(strcmp(argv[i],"--tiles")==0 && !tile_path && i+1<argc)
            tile_path=argv[++i];
        else if(strcmp(argv[i],"--records")==0 && !record_path && i+1<argc)
            record_path=argv[++i];
        else if(strcmp(argv[i],"--object-types")==0 && !object_types_path &&
                i+1<argc)
            object_types_path=argv[++i];
        else if(strcmp(argv[i],"--scenes")==0 && !scene_path && i+1<argc)
            scene_path=argv[++i];
        else if(strcmp(argv[i],"--nametable")==0 && !name_table_path &&
                i+1<argc)
            name_table_path=argv[++i];
        else if(strcmp(argv[i],"--patterns")==0 && !pattern_path &&
                i+1<argc)
            pattern_path=argv[++i];
        else {
            fputs("usage: ys-native-game [--smoke] [--tiles FILE] [--records FILE] [--object-types FILE] [--scenes FILE] [--nametable FILE] [--patterns FILE]\n",stderr);
            return EXIT_FAILURE;
        }
    }
    if(pattern_path && !name_table_path) {
        fputs("--patterns requires --nametable FILE\n",stderr);
        return EXIT_FAILURE;
    }
    if(object_types_path && !record_path) {
        fputs("--object-types requires --records FILE\n",stderr);
        return EXIT_FAILURE;
    }
    if(smoke_projection && (!smoke || !record_path)) {
        fputs("--smoke-projection requires --smoke and --records FILE\n",stderr);
        return EXIT_FAILURE;
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
    YsPcRecords source_records;
    bool have_records=false;
    if(record_path) {
        FILE *fp=fopen(record_path,"rb");
        have_records=fp && ys_pc_records_load(fp,&source_records);
        if(fp) fclose(fp);
        if(!have_records) {
            fprintf(stderr,"PC-2 invalid derived source record data: %s\n",
                    record_path);
            SDL_DestroyTexture(atlas);
            SDL_DestroyRenderer(r);SDL_DestroyWindow(w);SDL_Quit();
            return EXIT_FAILURE;
        }
    }
    YsPcObjectTypes object_types;
    bool have_object_types=false;
    if(object_types_path) {
        FILE *fp=fopen(object_types_path,"rb");
        have_object_types=fp && ys_pc_object_types_load(fp,&object_types);
        if(fp) fclose(fp);
        if(!have_object_types) {
            fprintf(stderr,"PC-4 invalid source object type table: %s\n",
                    object_types_path);
            SDL_DestroyTexture(atlas);
            SDL_DestroyRenderer(r);SDL_DestroyWindow(w);SDL_Quit();
            return EXIT_FAILURE;
        }
    }
    YsPcSceneDirectory scenes;
    bool have_scenes=false;
    if(scene_path) {
        FILE *fp=fopen(scene_path,"rb");
        have_scenes=fp && ys_pc_scenes_load(fp,&scenes);
        if(fp) fclose(fp);
        if(!have_scenes) {
            fprintf(stderr,"PC-5 invalid source scene directory: %s\n",scene_path);
            SDL_DestroyTexture(atlas);
            SDL_DestroyRenderer(r);SDL_DestroyWindow(w);SDL_Quit();
            return EXIT_FAILURE;
        }
    }
    YsPcNameTable name_table;
    bool have_name_table=false;
    if(name_table_path) {
        FILE *fp=fopen(name_table_path,"rb");
        have_name_table=fp && ys_pc_nametable_load(fp,&name_table);
        if(fp) fclose(fp);
        if(!have_name_table) {
            fprintf(stderr,"PC-6 invalid source name-table asset: %s\n",
                    name_table_path);
            SDL_DestroyTexture(atlas);
            SDL_DestroyRenderer(r);SDL_DestroyWindow(w);SDL_Quit();
            return EXIT_FAILURE;
        }
    }
    SDL_Texture *pattern_preview=NULL;
    YsPcPatternCoverage coverage={0};
    if(pattern_path) {
        FILE *fp=fopen(pattern_path,"rb");
        YsPcPatterns p;
        bool valid=fp && ys_pc_patterns_load(fp,&p);
        if(fp) fclose(fp);
        if(!valid) {
            fprintf(stderr,"PC-7 invalid source pattern data: %s\n",pattern_path);
            SDL_DestroyTexture(atlas);
            SDL_DestroyRenderer(r);SDL_DestroyWindow(w);SDL_Quit();
            return EXIT_FAILURE;
        }
        uint8_t indices[YS_PC_PREVIEW_W*YS_PC_PREVIEW_H];
        uint8_t rgb[YS_PC_PREVIEW_W*YS_PC_PREVIEW_H*3];
        if(!ys_pc_patterns_preview(&p,&name_table,indices,&coverage)) {
            fputs("PC-7 name-table/pattern composite failed\n",stderr);
            SDL_DestroyTexture(atlas);
            SDL_DestroyRenderer(r);SDL_DestroyWindow(w);SDL_Quit();
            return EXIT_FAILURE;
        }
        for(size_t i=0;i<sizeof(indices);++i) {
            uint8_t shade=(uint8_t)(indices[i]*17u);
            rgb[3u*i]=indices[i]==255u?255u:shade;
            rgb[3u*i+1u]=indices[i]==255u?0u:shade;
            rgb[3u*i+2u]=indices[i]==255u?255u:shade;
        }
        pattern_preview=SDL_CreateTexture(r,SDL_PIXELFORMAT_RGB24,
                          SDL_TEXTUREACCESS_STATIC,
                          YS_PC_PREVIEW_W,YS_PC_PREVIEW_H);
        if(!pattern_preview ||
           SDL_UpdateTexture(pattern_preview,NULL,rgb,YS_PC_PREVIEW_W*3)!=0) {
            fprintf(stderr,"PC-7 SDL texture: %s\n",SDL_GetError());
            SDL_DestroyTexture(pattern_preview);
            SDL_DestroyTexture(atlas);
            SDL_DestroyRenderer(r);SDL_DestroyWindow(w);SDL_Quit();
            return EXIT_FAILURE;
        }
    }
    bool show_pattern_preview=pattern_preview!=NULL;
    bool show_name_table=have_name_table && !show_pattern_preview;
    bool show_scenes=have_scenes && !show_name_table && !show_pattern_preview;
    unsigned scene_idx=0u, bank1_idx=0u;
    bool show_records=have_records && !show_scenes && !show_name_table && !show_pattern_preview;
    bool show_projection=smoke_projection;
    unsigned current_group=0u;
    bool show_atlas=atlas!=NULL && !show_records && !show_scenes && !show_name_table && !show_pattern_preview;
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
            if(ev.type==SDL_KEYDOWN && !ev.key.repeat) {
                if(atlas && ev.key.keysym.sym==SDLK_F2) {
                    show_atlas=!show_atlas;
                    if(show_atlas) {show_records=false;show_scenes=false;show_name_table=false;show_pattern_preview=false;}
                }
                if(have_records && ev.key.keysym.sym==SDLK_F3) {
                    show_records=!show_records;
                    if(show_records) {show_atlas=false;show_scenes=false;show_name_table=false;show_pattern_preview=false;}
                }
                if(have_records && ev.key.keysym.sym==SDLK_F4) {
                    show_records=true;
                    show_atlas=false;
                    show_scenes=false;
                    show_name_table=false;show_pattern_preview=false;
                    show_projection=!show_projection;
                }
                if(have_scenes && ev.key.keysym.sym==SDLK_F5) {
                    show_scenes=!show_scenes;
                    if(show_scenes) {show_atlas=false;show_records=false;show_name_table=false;show_pattern_preview=false;}
                }
                if(have_name_table && ev.key.keysym.sym==SDLK_F8) {
                    show_name_table=!show_name_table;
                    if(show_name_table) {
                        show_atlas=false;
                        show_records=false;
                        show_scenes=false;
                        show_pattern_preview=false;
                    }
                }
                if(pattern_preview && ev.key.keysym.sym==SDLK_F9) {
                    show_pattern_preview=!show_pattern_preview;
                    if(show_pattern_preview) {
                        show_atlas=false;
                        show_records=false;
                        show_scenes=false;
                        show_name_table=false;
                    }
                }
                if(show_scenes && ev.key.keysym.sym==SDLK_F6)
                    scene_idx=(scene_idx+1u)%YS_PC_SCENE_DISPATCH_COUNT;
                if(show_scenes && ev.key.keysym.sym==SDLK_F7)
                    bank1_idx=(bank1_idx+1u)%YS_PC_BANK1_SCENE_ENTRY_COUNT;
                if(show_records && ev.key.keysym.sym==SDLK_PAGEUP)
                    current_group=(current_group+YS_PC_GROUP_COUNT-1u)%
                                  YS_PC_GROUP_COUNT;
                if(show_records && ev.key.keysym.sym==SDLK_PAGEDOWN)
                    current_group=(current_group+1u)%YS_PC_GROUP_COUNT;
            }
        }
        Uint64 now=SDL_GetPerformanceCounter();
        double elapsed=(double)(now-prior)/freq;
        prior=now;
        accumulator+=elapsed>0.25?0.25:elapsed;
        unsigned buttons=(show_atlas || show_records || show_scenes || show_name_table || show_pattern_preview)?0u:read_buttons(pad);
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
        if(show_pattern_preview && pattern_preview)
            snprintf(title,sizeof(title),
                     "M43/M44 SOURCE index-gray | 384 tiles |"
                     " matched %u, unresolved %u | NO CRAM/map | F9",
                     coverage.matched_cells,coverage.unresolved_cells);
        else if(have_name_table && show_name_table)
            snprintf(title,sizeof(title),
                     "Original init VRAM $3900-$3EFF: 768 tile words | "
                     "INDEX gray ONLY, NOT world map | F8");
        else if(have_scenes && show_scenes)
            snprintf(title,sizeof(title),
                     "Source dispatch C119=%u -> $%04X | B1[%u]=$%04X"
                     " | NO map | F5/F6/F7",
                     scene_idx,scenes.fixed_handlers[scene_idx],
                     bank1_idx,scenes.bank1_entries[bank1_idx]);
        else if(have_records && show_records)
            snprintf(title,sizeof(title),
                     "Bank7 %s NOT map | group %u/22 $%04X count %u |"
                     " F4: plot/bytes, PgUp/PgDn",
                     show_projection?"work-field plot,":"source bytes,",
                     current_group+1u,
                     source_records.groups[current_group].source_pc,
                     source_records.groups[current_group].count);
        else if(atlas && show_atlas)
            snprintf(title,sizeof(title),
                     "Ys bank-3 source tiles (176) | grayscale PREVIEW | F2: room");
        else if(atlas)
            snprintf(title,sizeof(title),
                     "Ys PC placeholder room | F2: authentic bank-3 tile gallery");
        if(show_records && have_object_types) {
            size_t length=strlen(title);
            if(length+13u<sizeof(title))
                strcat(title," | PC4 types");
        }
        SDL_SetWindowTitle(w,title);
        draw_game(r,&game,atlas,show_atlas,
                  have_records?&source_records:NULL,show_records,current_group,
                  show_projection,
                  have_object_types?&object_types:NULL,
                  have_scenes?&scenes:NULL,show_scenes,scene_idx,bank1_idx,
                  have_name_table?&name_table:NULL,show_name_table,
                  pattern_preview,show_pattern_preview);
        if(smoke && game.frame>=12u) running=false;
        SDL_Delay(1);
    }
    if(pad) SDL_GameControllerClose(pad);
    SDL_DestroyTexture(pattern_preview);
    SDL_DestroyTexture(atlas);
    SDL_DestroyRenderer(r);SDL_DestroyWindow(w);SDL_Quit();
    return EXIT_SUCCESS;
}
