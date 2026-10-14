#ifndef YS_PC_GAME_H
#define YS_PC_GAME_H
#include <stdint.h>
#include <stdbool.h>
#include "pc_content.h"

enum {
    YS_PC_UP=1u, YS_PC_DOWN=2u, YS_PC_LEFT=4u, YS_PC_RIGHT=8u,
    YS_PC_START=16u
};
typedef enum {
    YS_PC_TITLE, YS_PC_PLAY, YS_PC_CLEAR, YS_PC_DEAD
} YsPcStage;
typedef struct {
    YsPcStage stage;
    int x, y, foe_x, foe_y, hp, foe_hp, defeats;
    unsigned frame, move_delay;
    /* Owned validated scene snapshot: deterministic restart and no
       dangling registry pointers. Still only a PLACEHOLDER test room. */
    YsPcSceneContent scene;
} YsPcGame;

/* PC-0 API continues to use the identical original placeholder room. */
char ys_pc_tile(int x,int y);
void ys_pc_game_reset(YsPcGame *game);
void ys_pc_game_tick(YsPcGame *game,unsigned buttons);

/* PC-10 experimental engine content seam, not an original Ys game map
   or shipping data-only mod-loader contract. Invalid input leaves the
   gameplay state unchanged. */
bool ys_pc_game_reset_scene(YsPcGame *game,const YsPcSceneContent *scene);
/* Resolve a stable symbolic ID from a validated catalog and copy
   its scene. Missing/invalid ID leaves current game state untouched. */
bool ys_pc_game_reset_named_scene(YsPcGame *game,
                                  const YsPcContentCatalog *catalog,
                                  const char *scene_id);
char ys_pc_game_tile(const YsPcGame *game,int x,int y);
#endif
