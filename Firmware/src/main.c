
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

#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <inttypes.h>
#include "nvs.h"
#include "nvs_flash.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "esp_adc/adc_oneshot.h"
#include"driver/uart.h"


#include "Bluetooth.h"


 /* Task handle*/
TaskHandle_t SENDtaskhandle;
TaskHandle_t CMtaskhandle;
TaskHandle_t CONFtaskhandle;
TaskHandle_t CDtaskhandle;

QueueHandle_t send_data_queue = NULL;
QueueHandle_t sampling_data_queue = NULL;
QueueHandle_t compress_data_queue = NULL;
QueueHandle_t receive_config_queue = NULL;

esp_timer_handle_t sampling_timer=NULL;

static int send_data_buffer[64];
static int compress_data_buffer[256];
int step_val=0;
bool isstep=false;
int step_len=0;

/**
 * @brief There's 3 mode of operation: 
 * 
 * - mode 0 is normal step operation
 * 
 * - mode 1 is compression mode operation 
 * 
 * - mode 3 is continous mode operation
 * 
 */
int mode;


Model model1={
    .name = NULL,
    .SM_Size = {0,0},
    .SM = NULL,
    .is_changed = false
};


void send_data(void *pvParameters){
    Compressed_data *s;
    for(;;){
        if(xQueueReceive(send_data_queue, &s, portMAX_DELAY)==pdTRUE){
            if(mode==0)
            {
                //Sending data on normal step mode
                uint8_t send_buffer[128*sizeof(int)]={0};
                memcpy(send_buffer,s->data,128*sizeof(int));
                    if(spp_conn_handle !=0){
                        esp_spp_write(spp_conn_handle,sizeof(send_buffer),send_buffer);
                        //printf("%02x %02x %02x %02x\n",send_buffer[0],send_buffer[1],send_buffer[2],send_buffer[3]);
                    }
                vTaskDelay(100);
                memcpy(send_buffer,s->data+128*sizeof(int),128*sizeof(int));
                    if(spp_conn_handle !=0){
                        esp_spp_write(spp_conn_handle,sizeof(send_buffer),send_buffer);
                        //printf("%02x %02x %02x %02x\n",send_buffer[0],send_buffer[1],send_buffer[2],send_buffer[3]);
                    }
            
            }else if (mode==1)
            {
                //Sending data on compression mode
                printf("Sending_data \n");
                int row = model1.SM_Size[0];
                uint8_t send_buffer[row*sizeof(float)+sizeof(s->max)+sizeof(s->min)];
                memcpy(&send_buffer[0],s->data,row*sizeof(float));

                memcpy(&send_buffer[row*4],&s->max,sizeof(s->max));
                int max = 0; 
                memcpy(&max, &s->max,sizeof(s->max));

                memcpy(&send_buffer[row*4+4],&s->min,sizeof(s->min));
                int min = 0; 
                memcpy(&min, &s->min,sizeof(s->min));

                if(spp_conn_handle !=0){
                    esp_spp_write(spp_conn_handle,sizeof(send_buffer),send_buffer);
                    printf("%f\n",*(float*)s->data);
                    printf("%d\n",max);
                    printf("%d\n",min);
                }

            }else if (mode == 3)
            {
                //Sending data on normal continous mode
                uint8_t send_buffer[64*sizeof(int)]={0};
                memcpy(send_buffer,s->data,64*sizeof(int));
                if(spp_conn_handle !=0){
                    esp_spp_write(spp_conn_handle,sizeof(send_buffer),send_buffer);
                }
            }
        
            free(s->data);
            free(s);
        }    
    }
}

//Task for processing data received from the sampling using timer interrupt on continous mode
void continous_data_task(void* pvParameters){
    ESP_LOGI("TASK","Continous Data task Start");
    for(;;){
        
        for(int i = 0; i<64;i++){
            int single_sample = 0;
            xQueueReceive(sampling_data_queue,&single_sample,portMAX_DELAY);
            send_data_buffer[i] = single_sample;
        }

        Compressed_data *s = malloc(sizeof(Compressed_data));
        s->data = malloc(64*sizeof(int));
        memcpy(s->data,send_data_buffer,64*sizeof(int));
        if(xQueueSendToBack(send_data_queue,&s,0) == errQUEUE_FULL){
            printf("Send Queue Full");
        }
    }       
}

//Task for processing data received from the sampling using timer interrupt on step and compression mode
void compression_data_task(void* pvParameters){
    ESP_LOGI("TASK","Compression Data Start");
    for(;;){

        for(int i = 0; i<256;i++){
            int single_sample = 0;
            xQueueReceive(compress_data_queue,&single_sample,portMAX_DELAY);
            compress_data_buffer[i] = single_sample;
        }

        if(isstep == true){
                step_val++;
                if(step_val>=step_len){
                    isstep=false;
                    step_val=0;
                    step_len=0;
                    esp_timer_stop(sampling_timer);
                }
            }

        Compressed_data *s = malloc(sizeof(Compressed_data));
        if (mode == 0)
        {
            //processing data to be sent for normal step mode
            s->data = malloc(256*sizeof(int));
            memcpy(s->data,compress_data_buffer,256*sizeof(int));
            if(xQueueSendToBack(send_data_queue,&s,0) == errQUEUE_FULL){
                printf("Send Queue Full");
            }
        }
        else if (mode == 1)
        {
            //processing data, normalization and matrix multiplication for compression mode
            s->data = malloc(model1.SM_Size[0]*sizeof(float));

            //Find MAX
            s->max = compress_data_buffer[0]; 
            for (int i = 1; i < 256; i++) {
                if (compress_data_buffer[i] > s->max) {
                    s->max = compress_data_buffer[i]; 
                }
            }

            //Find MIN
            s->min = compress_data_buffer[0];  
            for (int i = 1; i < 256; i++) {
                if (compress_data_buffer[i] < s->min) {
                    s->min = compress_data_buffer[i];  
                }
            }

            //Normalize
            float normalized_array[256]={0};
            float div = (float)s->max-s->min; 
            if( div == 0){
                printf("Div by 0");
                vTaskDelete(NULL);
            }

            for (int i=0; i<256;i++){
                normalized_array[i]= (compress_data_buffer[i]-s->min)/div;
            }
            
            //MatMul
            for (int i=0; i<model1.SM_Size[0];i++){
                float acc_buff = 0;

                for(int j=0;j<256;j++){
                    //J/8 bytenya, lalu geser kiri sebanyak bit keberapa
                    // terus di mask dengan 1000_0000 lalu geser ke paling kanan

                    if((model1.SM[32 *i +(j/8)]<<(j%8)&0x80)>>7 == 1){
                        acc_buff = acc_buff + normalized_array[j];
                    }else{
                        acc_buff = acc_buff - normalized_array[j];
                    }
                }
                memcpy(s->data+i*4,&acc_buff,sizeof(float));
            }

            // Sending queue to send task
            if(xQueueSendToBack(send_data_queue,&s,0) == errQUEUE_FULL){
                printf("Send Queue Full");
            }
        }
        // memset(&send_data_buffer,0,sizeof(send_data_buffer));      
    }
}

//Timer interrupt for sampling data
void IRAM_ATTR sensor_sampling( void*arg ){

    adc_oneshot_unit_handle_t adc_handle = (adc_oneshot_unit_handle_t) arg;
    int sampling_val = 0;
    adc_oneshot_read(adc_handle,ADC_CHANNEL_3,&sampling_val);
    if(mode == 3){
    xQueueSendFromISR(sampling_data_queue,&sampling_val,NULL);
    }else
    {
        xQueueSendFromISR(compress_data_queue,&sampling_val,NULL);    
    }
}

// Step (sensor sampling) -> (compress data) -> (send_data) 

void app_main(void)
{
    //NVS Init
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK( ret );
    bluetooth_config();

    //Create queue
    send_data_queue = xQueueCreate(2, sizeof(Compressed_data *));
    sampling_data_queue = xQueueCreate(256, sizeof(int));
    compress_data_queue = xQueueCreate(512,sizeof(int));
    receive_config_queue = xQueueCreate(10, sizeof(Config_parameter *));


    // ADC Init //
    adc_oneshot_unit_handle_t adc2_handle;
    adc_oneshot_unit_init_cfg_t init_config2 = {
        .unit_id = ADC_UNIT_2,
    };
    ESP_ERROR_CHECK(adc_oneshot_new_unit(&init_config2, &adc2_handle));

    adc_oneshot_chan_cfg_t config = {
        .atten = ADC_ATTEN_DB_12,
        .bitwidth = ADC_BITWIDTH_DEFAULT,
    };
    ESP_ERROR_CHECK(adc_oneshot_config_channel(adc2_handle, ADC_CHANNEL_3, &config));

    esp_timer_create_args_t sampling_timer_cfg = {
        .callback = sensor_sampling,
        .arg = adc2_handle,
        .name = "Sampling",
        .dispatch_method = ESP_TIMER_ISR
    };

    ESP_ERROR_CHECK(esp_timer_create(&sampling_timer_cfg,&sampling_timer));
    
    BaseType_t r;
    r =xTaskCreatePinnedToCore(send_data,"Send_data_Task",4096,NULL,0,&SENDtaskhandle,0);
    if (r != pdPASS){ESP_LOGI("MAIN", "Send data task not created");}

    r = xTaskCreatePinnedToCore(compression_data_task,"Compression Data Task",4096,NULL,0,&CMtaskhandle,1);
    if (r != pdPASS){ESP_LOGI("MAIN", "Compression data task not created");}

    r = xTaskCreatePinnedToCore(config_data,"Configuration Data",2048,NULL,1,&CONFtaskhandle,1);
    if (r != pdPASS){ESP_LOGI("MAIN", "config task not created");}

    r = xTaskCreatePinnedToCore(continous_data_task,"Continous Data Task",4096,NULL,0,&CDtaskhandle,1);
    if (r != pdPASS){ESP_LOGI("MAIN", "Continous task not created");}

}