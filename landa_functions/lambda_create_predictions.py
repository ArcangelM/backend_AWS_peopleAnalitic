# lambda function
def lambda_handler(event, context):
    
    BUCKET_NAME = event["Records"][0]["s3"]["bucket"]["name"]
    key_bucket_origen = event["Records"][0]["s3"]["object"]["key"]
    
    # descargamos archivo csv a un archivo temporal local
    local_file_name = '/tmp/temporal.csv'  #
    s3.Bucket(BUCKET_NAME).download_file(key_bucket_origen, local_file_name)
   
    with open('/tmp/temporal.csv', 'r') as infile:
        reader = list(csv.reader(infile))

    data = np.array(reader)

    id_estudiantes= list(data[:,0])
    data_to_model = data [:,1:]

    payload = np2csv(data_to_model) #convierto data que va al modelo en csv
    print(payload)

    
    response = runtime.invoke_endpoint(EndpointName=ENDPOINT_NAME,
                                       ContentType='text/csv',
                                       Body=payload)
    print('respuesta', response)

    #se decodifica el la respuesta del modelo con las predicciones
    result = response['Body'].read().decode()
   
    #se redondean los resultados a enteros, laos resultados llegan en formato sting
    re = [np.round(float(resp)) for resp in result.split(',')]
    print('resultado', re)

    predicted_label = ['En riesgo' if pred == 1 else 'No riesgo' for pred in re] #convierto las salidas a frase
    print('chape de label:',len(predicted_label))
    print('chape de estu:',len(id_estudiantes))
    #arreglo de id de estudiantes y predicciones
    reporte = (np.array([id_estudiantes,predicted_label])).T
    print("reporte array",reporte)
    
    reporte = list(reporte) # lista de id_estudiantes con su respectiva prediccion.
    print('reporte final', reporte)
    
    with open('/tmp/temporal_reporte.csv', 'w', newline='') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(['Id_estudiantes','Prediccion'])
        for line in reporte:  # reverse order
            writer.writerow(line)

    # secarga el csv con el reporte temporal desde la carpeta tmp a el s3 key destino
    key_aux=key_bucket_origen.split('/')
    key_bucket_destino= '{}/reporte_{}'.format(key_aux[0],key_aux[1])
    bucket2.upload_file('/tmp/temporal_reporte.csv', key_bucket_destino)
    
    return {
        'message': 'success!!'
    }