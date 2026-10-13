/* SDL2 is optional; this displays the synthetic mode-4 diagnostic only.
   It is not the native Ys title/game and does not load a ROM. */
#define SDL_MAIN_HANDLED
#include <SDL.h>
#include "sms_clock.h"
#include "sms_video.h"
#include "video_fixture.h"
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    if(SDL_Init(SDL_INIT_VIDEO | SDL_INIT_EVENTS)!=0) {
        fprintf(stderr,"SDL2 initialization: %s\n",SDL_GetError());
        return EXIT_FAILURE;
    }
    SDL_Window *window=SDL_CreateWindow(
        "Ys SMS video diagnostic - NOT gameplay",
        SDL_WINDOWPOS_CENTERED,SDL_WINDOWPOS_CENTERED,768,576,
        SDL_WINDOW_SHOWN | SDL_WINDOW_RESIZABLE);
    if(!window) {
        fprintf(stderr,"SDL2 window: %s\n",SDL_GetError());
        SDL_Quit();return EXIT_FAILURE;
    }
    SDL_Renderer *renderer=SDL_CreateRenderer(
        window,-1,SDL_RENDERER_ACCELERATED|SDL_RENDERER_PRESENTVSYNC);
    if(!renderer) renderer=SDL_CreateRenderer(window,-1,SDL_RENDERER_SOFTWARE);
    SDL_Texture *texture=renderer?SDL_CreateTexture(
        renderer,SDL_PIXELFORMAT_RGB24,SDL_TEXTUREACCESS_STREAMING,
        YS_SMS_SCREEN_WIDTH,YS_SMS_SCREEN_HEIGHT):NULL;
    YsSmsVdp *vdp=malloc(sizeof(*vdp));
    uint8_t *rgb=malloc(YS_SMS_RGB_BYTES);
    if(!renderer || !texture || !vdp || !rgb ||
       SDL_RenderSetLogicalSize(renderer,YS_SMS_SCREEN_WIDTH,
                                YS_SMS_SCREEN_HEIGHT)!=0) {
        fprintf(stderr,"SDL2 renderer or memory: %s\n",SDL_GetError());
        free(vdp);free(rgb);SDL_DestroyTexture(texture);
        SDL_DestroyRenderer(renderer);SDL_DestroyWindow(window);
        SDL_Quit();return EXIT_FAILURE;
    }
    ys_sms_video_fixture_init(vdp);
    vdp->registers[1]|=0x20u;
    YsSmsClock clock;
    bool running=ys_sms_clock_reset(&clock,YS_SMS_NTSC);
    unsigned frame=0;
    while(running) {
        SDL_Event event;
        while(SDL_PollEvent(&event)) {
            if(event.type==SDL_QUIT ||
               (event.type==SDL_KEYDOWN &&
                event.key.keysym.sym==SDLK_ESCAPE)) running=false;
        }
        if(!running) break;
        uint32_t start=SDL_GetTicks();
        ys_sms_video_fixture_animate(vdp,frame++);
        if(!ys_sms_clock_advance(&clock,vdp,ys_sms_clock_tstates_per_frame(&clock)) ||
           !ys_sms_video_render(vdp,rgb,YS_SMS_RGB_BYTES,NULL) ||
           SDL_UpdateTexture(texture,NULL,rgb,YS_SMS_SCREEN_WIDTH*3)!=0 ||
           SDL_RenderClear(renderer)!=0 ||
           SDL_RenderCopy(renderer,texture,NULL,NULL)!=0) {
            fprintf(stderr,"SDL2 diagnostic frame: %s\n",SDL_GetError());
            running=false;
            break;
        }
        SDL_RenderPresent(renderer);
        uint8_t status=0u;
        if(!ys_sms_vdp_read(vdp,0xBF,&status) || (status&0x80u)==0u) {
            fputs("diagnostic VBlank status missing\n",stderr);
            break;
        }
        /* Wall-clock display cadence is approximate. This viewer cannot
           establish Z80 T-state timing or game-frame equivalence. */
        uint32_t elapsed=SDL_GetTicks()-start;
        if(elapsed<16u) SDL_Delay(16u-elapsed);
    }
    free(vdp);free(rgb);
    SDL_DestroyTexture(texture);
    SDL_DestroyRenderer(renderer);
    SDL_DestroyWindow(window);
    SDL_Quit();
    return EXIT_SUCCESS;
}
