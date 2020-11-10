"""
    LAMBDA: get_urls_reporte
    Esta funcion lambda  genera las URL de descarga de los archivos reporves CSV que 
    se encuentran en los bucket de S3.
    Es invocada atravis de la API gateway via METODO GET recibiendo como parametro el nombre de la IES que quiere
    obtener los links de descargas de los reportes. ej: {"nombre_ies": "univalle" }.
    
    La funcion Lambda retornará un array con la lista de los links de descargas (estos links tendran una caducidad de una hora).
    

"""

#Importacion de librerias
import json
import logging
import boto3
import datetime
from boto3 import client
from botocore.exceptions import ClientError




def create_presigned_url(bucket_name, object_name, expiration=3600):
    """Funcion que genera un link de descarga de un objeto en s3 con un tiempo de expiracion

    :param bucket_name: string
    :param object_name: string
    :param expiration: tiempo en segundos de la duracion de valides del link
    :return: retorna una Url prefirmada, si hay error returns None.
    """

    # se genera un nuevo cliente s3
    s3_client = boto3.client('s3')
    try:
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': object_name},
                                                    ExpiresIn=expiration)
    except ClientError as e:
        logging.error(e)
        return None

    # la respuesta contienen la URL 
    
    return response



def lambda_handler(event, context):
    
    #Bucket definido para almacenar los reportes
    BUCKET_NAME ='reportesies'
    
    print("Received event: " + json.dumps(event, indent=2))
    nombre_ies = json.loads(json.dumps(event))['nombre_ies']
   
    prefix_ies ="{}/".format(nombre_ies) 
    
    #se crea un cliente s3
    conn = client('s3') 
    list_urls=[]
    for key in conn.list_objects(Bucket=BUCKET_NAME,Prefix=prefix_ies)['Contents']:
        print('esto es el key ', key['Key'][ :len(prefix_ies) ])
        if (key['Key'][-4:] =='.csv' and key['Key'][ :len(prefix_ies) ] == prefix_ies):
            
            
            url= create_presigned_url(BUCKET_NAME, key['Key'], expiration=3600)
            if url != None:
                list_urls.append(
                        {
                            'url':url,
                            'file_name': key['Key'][ len(prefix_ies): ],
                            'date': '{:%Y %m %d %H:%M:%S}'.format(key['LastModified'])
                        }
                    )
                print('fecha: {:%Y %m %d %H:%M:%S}'.format(key['LastModified']))
    print(list_urls)
    
    
    return {
        'statusCode': 200,
        'body': json.dumps('Urls creadas!'),
        'data':list_urls
        
    }