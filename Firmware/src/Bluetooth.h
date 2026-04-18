/*
   Copyright 2026 Joseph Maximillian Bonaventura Chico Reginald Jansen

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
 */

#include <string.h>

#include "esp_bt.h"
#include "esp_bt_main.h"
#include "esp_gap_bt_api.h"
#include "esp_bt_device.h"
#include "esp_spp_api.h"
#include "esp_log.h"
#include "esp_heap_caps.h"
#include "esp_timer.h"
#include "esp_gdbstub.h"

#include "time.h"
#include "sys/time.h"

#define SPP_TAG "SPP_SENSOR"

extern uint32_t spp_conn_handle;
extern esp_timer_handle_t sampling_timer;
extern bool isstep;
extern bool isconfig;
extern int step_len;
extern int mode;
extern const float Sensing_matrix[104][256];
extern QueueHandle_t receive_config_queue;


typedef struct 
{
    int data_size;
    uint8_t * config_param_address;
}Config_parameter;

typedef struct {
    int min;
    int max;
    void *data;
}Compressed_data;

typedef struct {
    char* name;
    uint16_t SM_Size[2];
    uint8_t * SM;
    bool is_changed;
} Model;

extern Model model1;

void config_data(void * pvParameters);
void bluetooth_config(void);


