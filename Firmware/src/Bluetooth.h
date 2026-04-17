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
extern int step_mode;
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
} Compressed_data;

typedef struct {
    char* name;
    uint16_t SM_Size[2];
    uint8_t * SM;
    bool is_changed;
} Model;

extern Model model1;

void config_data(void * pvParameters);
void bluetooth_config(void);


