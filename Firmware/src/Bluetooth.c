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

#include "Bluetooth.h"

#define SPP_SERVER_NAME "SPP_SERVER"

static const char local_device_name[] = CONFIG_LOCAL_DEVICE_NAME;

uint32_t spp_conn_handle =0;
 
static const esp_spp_mode_t esp_spp_mode = ESP_SPP_MODE_CB;
static const bool esp_spp_enable_l2cap_ertm = true;
static struct timeval time_new, time_old;

static long data_num = 0;

static const esp_spp_sec_t sec_mask = ESP_SPP_SEC_AUTHENTICATE;
static const esp_spp_role_t role_slave = ESP_SPP_ROLE_SLAVE;


static void esp_spp_cb(esp_spp_cb_event_t event, esp_spp_cb_param_t *param)
 {
     char bda_str[18] = {0};
 
     switch (event) {
     case ESP_SPP_INIT_EVT:
         if (param->init.status == ESP_SPP_SUCCESS) {
             ESP_LOGI(SPP_TAG, "ESP_SPP_INIT_EVT");
             esp_spp_start_srv(sec_mask, role_slave, 0, SPP_SERVER_NAME);
         } else {
             ESP_LOGE(SPP_TAG, "ESP_SPP_INIT_EVT status:%d", param->init.status);
         }
         break;
     case ESP_SPP_DISCOVERY_COMP_EVT:
         ESP_LOGI(SPP_TAG, "ESP_SPP_DISCOVERY_COMP_EVT");
         break;
     case ESP_SPP_OPEN_EVT:
         ESP_LOGI(SPP_TAG, "ESP_SPP_OPEN_EVT");
         break;
     case ESP_SPP_CLOSE_EVT:
         ESP_LOGI(SPP_TAG, "ESP_SPP_CLOSE_EVT status:%d handle:%"PRIu32" close_by_remote:%d", param->close.status,
                  param->close.handle, param->close.async);
         
        //Close Connection and stop timer
         spp_conn_handle = 0;
         esp_timer_stop(sampling_timer);
         break;
     case ESP_SPP_START_EVT:
         if (param->start.status == ESP_SPP_SUCCESS) {
             ESP_LOGI(SPP_TAG, "ESP_SPP_START_EVT handle:%"PRIu32" sec_id:%d scn:%d", param->start.handle, param->start.sec_id,
                      param->start.scn);
             esp_bt_gap_set_device_name(local_device_name);
             esp_bt_gap_set_scan_mode(ESP_BT_CONNECTABLE, ESP_BT_GENERAL_DISCOVERABLE);
         } else {
             ESP_LOGE(SPP_TAG, "ESP_SPP_START_EVT status:%d", param->start.status);
         }
         break;
     case ESP_SPP_CL_INIT_EVT:
         ESP_LOGI(SPP_TAG, "ESP_SPP_CL_INIT_EVT");
         break;
     case ESP_SPP_DATA_IND_EVT:
        
        //Receive Config
        if(isconfig){        
            Config_parameter* buffer = malloc(sizeof(Config_parameter));
            buffer->config_param_address = malloc(param->data_ind.len);
            if(buffer && buffer->config_param_address){
               
                memcpy(buffer->config_param_address,param->data_ind.data,param->data_ind.len);
                buffer->data_size =  param->data_ind.len;
                
                xQueueSendToBack(receive_config_queue,&buffer,0);
            }
        }else{

            if(strncmp((const char*)param->data_ind.data,"start",strlen("start"))==0){
                //Start normal continous mode
                printf("Timer Start");
                esp_timer_start_periodic(sampling_timer,2778);
                mode=3;
            }else if (strncmp((const char*)param->data_ind.data,"stop",strlen("stop"))==0)
            {
                //Stop normal continous mode
                printf("Timer Stop");
                esp_timer_stop(sampling_timer);
            }else if (strncmp((const char*)param->data_ind.data,"step0",strlen("step0"))==0)
            {
                char string[6]="";
                memcpy(string,param->data_ind.data,param->data_ind.len);
                step_len = *(param->data_ind.data + 5);
                mode = 0;
                printf("step_len %d\n",step_len);
                esp_timer_start_periodic(sampling_timer,2778);
                isstep = true;
            }else if (strncmp((const char*)param->data_ind.data,"step1",strlen("step1"))==0)
            {
                char string[6]="";
                memcpy(string,param->data_ind.data,param->data_ind.len);
                step_len = *(param->data_ind.data + 5);
                mode =1;
                printf("step_len %d\n",step_len);
                esp_timer_start_periodic(sampling_timer,2778);
                isstep = true;
            }else if (strncmp((const char*)param->data_ind.data,"config",strlen("config"))==0)
            {
                //Starting configuration mode
                if(spp_conn_handle !=0){
                        esp_spp_write(spp_conn_handle,strlen("ACK"),(uint8_t*)"ACK");
                        printf("ACK \n");
                }
                isconfig = true;
                ESP_LOGI("MODEL CONFIG","MODEL CONFIGURATION START");
            }else{
                printf("No");
            }
        }

         break;
     case ESP_SPP_CONG_EVT:
         ESP_LOGI(SPP_TAG, "ESP_SPP_CONG_EVT");
         break;
     case ESP_SPP_WRITE_EVT:
         //ESP_LOGI(SPP_TAG, "ESP_SPP_WRITE_EVT");
         break;
     case ESP_SPP_SRV_OPEN_EVT:
         ESP_LOGI(SPP_TAG, "ESP_SPP_SRV_OPEN_EVT status:%d handle:%"PRIu32", rem_bda:[%s]", param->srv_open.status,
                  param->srv_open.handle, bda2str(param->srv_open.rem_bda, bda_str, sizeof(bda_str)));
         gettimeofday(&time_old, NULL);
         spp_conn_handle = param->srv_open.handle;
         //assert(0);
         printf(" STACK %d \n", uxTaskGetStackHighWaterMark(NULL) );

         if(!heap_caps_check_integrity_all(true)){
            printf("Memmory Corruption");
         }
         break;
     case ESP_SPP_SRV_STOP_EVT:
         ESP_LOGI(SPP_TAG, "ESP_SPP_SRV_STOP_EVT");
         break;
     case ESP_SPP_UNINIT_EVT:
         ESP_LOGI(SPP_TAG, "ESP_SPP_UNINIT_EVT");
         break;
     default:
         break;
     }
}


void esp_bt_gap_cb(esp_bt_gap_cb_event_t event, esp_bt_gap_cb_param_t *param)
 {
     char bda_str[18] = {0};
 
     switch (event) {
     case ESP_BT_GAP_AUTH_CMPL_EVT:{
         if (param->auth_cmpl.stat == ESP_BT_STATUS_SUCCESS) {
             ESP_LOGI(SPP_TAG, "authentication success: %s bda:[%s]", param->auth_cmpl.device_name,
                      bda2str(param->auth_cmpl.bda, bda_str, sizeof(bda_str)));
         } else {
             ESP_LOGE(SPP_TAG, "authentication failed, status:%d", param->auth_cmpl.stat);
         }
         break;
     }
     case ESP_BT_GAP_PIN_REQ_EVT:{
         ESP_LOGI(SPP_TAG, "ESP_BT_GAP_PIN_REQ_EVT min_16_digit:%d", param->pin_req.min_16_digit);
         if (param->pin_req.min_16_digit) {
             ESP_LOGI(SPP_TAG, "Input pin code: 0000 0000 0000 0000");
             esp_bt_pin_code_t pin_code = {0};
             esp_bt_gap_pin_reply(param->pin_req.bda, true, 16, pin_code);
         } else {
             ESP_LOGI(SPP_TAG, "Input pin code: 1234");
             esp_bt_pin_code_t pin_code;
             pin_code[0] = '1';
             pin_code[1] = '2';
             pin_code[2] = '3';
             pin_code[3] = '4';
             esp_bt_gap_pin_reply(param->pin_req.bda, true, 4, pin_code);
         }
         break;
     }
 

     case ESP_BT_GAP_CFM_REQ_EVT:
         ESP_LOGI(SPP_TAG, "ESP_BT_GAP_CFM_REQ_EVT Please compare the numeric value: %06"PRIu32, param->cfm_req.num_val);
         esp_bt_gap_ssp_confirm_reply(param->cfm_req.bda, true);
         break;
     case ESP_BT_GAP_KEY_NOTIF_EVT:
         ESP_LOGI(SPP_TAG, "ESP_BT_GAP_KEY_NOTIF_EVT passkey:%06"PRIu32, param->key_notif.passkey);
         break;
     case ESP_BT_GAP_KEY_REQ_EVT:
         ESP_LOGI(SPP_TAG, "ESP_BT_GAP_KEY_REQ_EVT Please enter passkey!");
         break;

     case ESP_BT_GAP_MODE_CHG_EVT:
         ESP_LOGI(SPP_TAG, "ESP_BT_GAP_MODE_CHG_EVT mode:%d bda:[%s]", param->mode_chg.mode,
                  bda2str(param->mode_chg.bda, bda_str, sizeof(bda_str)));
         break;
 
     default: {
         ESP_LOGI(SPP_TAG, "event: %d", event);
         break;
     }
     }
     return;
}


void bluetooth_config(void){
    esp_err_t ret;
    char bda_str[18] = {0};
    ESP_ERROR_CHECK(esp_bt_controller_mem_release(ESP_BT_MODE_BLE)); 

    //Bluetooth Controller INIT
     esp_bt_controller_config_t bt_cfg = BT_CONTROLLER_INIT_CONFIG_DEFAULT();
     if ((ret = esp_bt_controller_init(&bt_cfg)) != ESP_OK) {
         ESP_LOGE(SPP_TAG, "%s initialize controller failed: %s", __func__, esp_err_to_name(ret));
         return;
     }
 
     if ((ret = esp_bt_controller_enable(ESP_BT_MODE_BTDM)) != ESP_OK) {
         ESP_LOGE(SPP_TAG, "%s enable controller failed: %s", __func__, esp_err_to_name(ret));
         return;
     }
 
     //Bluedroid INIT
     esp_bluedroid_config_t bluedroid_cfg = BT_BLUEDROID_INIT_CONFIG_DEFAULT();

     if ((ret = esp_bluedroid_init_with_cfg(&bluedroid_cfg)) != ESP_OK) {
         ESP_LOGE(SPP_TAG, "%s initialize bluedroid failed: %s", __func__, esp_err_to_name(ret));
         return;
     }
 
     if ((ret = esp_bluedroid_enable()) != ESP_OK) {
         ESP_LOGE(SPP_TAG, "%s enable bluedroid failed: %s", __func__, esp_err_to_name(ret));
         return;
     }
     
     //GAP function callback register
     if ((ret = esp_bt_gap_register_callback(esp_bt_gap_cb)) != ESP_OK) {
         ESP_LOGE(SPP_TAG, "%s gap register failed: %s", __func__, esp_err_to_name(ret));
         return;
     }
     
     //SPP function callback register
     if ((ret = esp_spp_register_callback(esp_spp_cb)) != ESP_OK) {
         ESP_LOGE(SPP_TAG, "%s spp register failed: %s", __func__, esp_err_to_name(ret));
         return;
     }
 
     //SPP Config 
     esp_spp_cfg_t bt_spp_cfg = {
         .mode = esp_spp_mode,
         .enable_l2cap_ertm = esp_spp_enable_l2cap_ertm,
         .tx_buffer_size = 0, 
     };
     if ((ret = esp_spp_enhanced_init(&bt_spp_cfg)) != ESP_OK) {
         ESP_LOGE(SPP_TAG, "%s spp init failed: %s", __func__, esp_err_to_name(ret));
         return;
     }
 
     esp_bt_sp_param_t param_type = ESP_BT_SP_IOCAP_MODE;
     esp_bt_io_cap_t iocap = ESP_BT_IO_CAP_IO;
     esp_bt_gap_set_security_param(param_type, &iocap, sizeof(uint8_t));
 
     esp_bt_pin_type_t pin_type = ESP_BT_PIN_TYPE_VARIABLE;
     esp_bt_pin_code_t pin_code;
     esp_bt_gap_set_pin(pin_type, 0, pin_code);
 
     ESP_LOGI(SPP_TAG, "Own address:[%s]", bda2str((uint8_t *)esp_bt_dev_get_address(), bda_str, sizeof(bda_str)));   
}