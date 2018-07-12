#ifndef REORG_OLD_LAYER_H
#define REORG_OLD_LAYER_H

#include "image.h"
#include "cuda.h"
#include "layer.h"
#include "network.h"

layer make_reorg_old_layer(int batch, int h, int w, int c, int stride, int reverse);
void resize_reorg_old_layer(layer *l, int w, int h);
void forward_reorg_old_layer(const layer l, network_state state);
void backward_reorg_old_layer(const layer l, network_state state);

#ifdef GPU
void forward_reorg_old_layer_gpu(layer l, network_state state);
void backward_reorg_old_layer_gpu(layer l, network_state state);
#endif

#endif

