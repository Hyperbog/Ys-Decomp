#ifndef YS_VIDEO_FIXTURE_H
#define YS_VIDEO_FIXTURE_H
#include "sms_vdp.h"

/* Synthetic, ROM-independent developer test scene, not Ys assets. */
void ys_sms_video_fixture_init(YsSmsVdp *vdp);

/* Deterministic demo motion; caller advances the VDP clock separately. */
void ys_sms_video_fixture_animate(YsSmsVdp *vdp, unsigned frame);
#endif
