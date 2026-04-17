#include <Bluetooth.h>


bool isconfig = false;

void config_data(void * pvParameters){
    Config_parameter * buffer;
    for(;;){
        if(xQueueReceive(receive_config_queue,&buffer,portMAX_DELAY)){
            if(buffer != NULL){
                static int sm_index = 0;
                if(strncmp((const char *)buffer->config_param_address,"M:",strlen("M:"))==0){
                    if(model1.name!=NULL){
                        free(model1.name);
                    }
                    model1.name = malloc(buffer->data_size-1);
                    strncpy(model1.name, (const char *)buffer->config_param_address+2,buffer->data_size-2);
                    model1.name[buffer->data_size-2] = '\0';
                    printf("datalen = %d \n", buffer->data_size);
                    printf("data = %s \n", model1.name);
                    if(spp_conn_handle !=0){
                        esp_spp_write(spp_conn_handle,strlen("ACK"),(uint8_t*)"ACK");
                        printf("ACK \n");
                    }
                }
                else if (strncmp((const char *)buffer->config_param_address,"S:",strlen("S:"))==0)
                {
                    
                    model1.SM_Size[0] = ((uint16_t) buffer->config_param_address[3] << 8) | buffer->config_param_address[2];
                    model1.SM_Size[1] = ((uint16_t) buffer->config_param_address[5] << 8) | buffer->config_param_address[4];
                    printf("SM size : (%d,%d) \n", model1.SM_Size[0],model1.SM_Size[1]);
                    
                    if(model1.SM != NULL){
                        free(model1.SM);
                    }
                    
                    model1.SM = malloc(model1.SM_Size[0] * 32);
                    if(model1.SM == NULL){
                        printf("Failed to allocate Memmory for SM !!!\n");
                    }else{
                        if(spp_conn_handle !=0){
                            esp_spp_write(spp_conn_handle,strlen("ACK"),(uint8_t*)"ACK");
                            printf("ACK \n");
                        }
                    }
                }
                else if (strncmp((const char *)buffer->config_param_address,"D:",strlen("D:"))==0)
                {
                    size_t in = buffer->data_size - 2;
                    memcpy(model1.SM + in * sm_index, buffer->config_param_address+2, in);
                    
                    //FOR Debugging SM
                    // printf("Data_buffer : ");
                    // for(size_t i =0;i<in; i++){
                    //     printf("%02x ",buffer->config_param_address[i+2]);
                    // }
                    // printf("\n");

                    // printf("Data_Model : ");
                    // for(size_t i =0;i<in; i++){
                    //     printf("%02x ",model1.SM[i+ in * sm_index]);
                    // }
                    // printf("\n");

                    sm_index++;
                    if(sm_index>model1.SM_Size[0]){
                        printf("ERROR SM dimensions have different values than specified!! \n");
                    }else
                    {
                        if(spp_conn_handle !=0){
                            esp_spp_write(spp_conn_handle,strlen("ACK"),(uint8_t*)"ACK");
                        }
                    }
                }
                else if (strncmp((const char *)buffer->config_param_address,"config_done",strlen("config_done"))==0)
                {
                    if(sm_index<model1.SM_Size[0]){
                        printf("ERROR SM dimensions have different values than specified!! \n");
                    }else
                    {
                        printf("%d",sm_index);
                        isconfig = false;
                        sm_index = 0;
                        if(spp_conn_handle !=0){
                            esp_spp_write(spp_conn_handle,strlen("ACK"),(uint8_t*)"ACK");
                            printf("ACK \n");
                            printf("SM Index : %d \n --CONFIG_DONE-- \n",sm_index);
                        }
                    }
                }
                free(buffer->config_param_address);
                free(buffer);
                buffer = NULL;
            }
        }
    }
}

