#ifndef YS_PC_GAME_H
#define YS_PC_GAME_H
#include <stdint.h>

enum { YS_PC_MAP_W=16, YS_PC_MAP_H=12 };
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
} YsPcGame;

/* Engine-only prototype. All map/content and art are placeholders. */
char ys_pc_tile(int x, int y);
void ys_pc_game_reset(YsPcGame *game);
void ys_pc_game_tick(YsPcGame *game, unsigned buttons);

#endif
