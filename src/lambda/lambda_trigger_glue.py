"""
Lambda function para acionar Glue Job
Acionada via S3 Event Notification (ObjectCreated)
Atende Requisito R3: Lambda aciona job ETL no Glue
"""

import json
import logging
import os
from datetime import datetime

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

glue_client = boto3.client('glue')


def lambda_handler(event, context):
    """
    Lambda handler - executado quando novo objeto é criado no S3 raw/
    """
    logger.info("="*70)
    logger.info("LAMBDA TRIGGER GLUE - INICIANDO")
    logger.info(f"Event: {json.dumps(event)}")
    logger.info("="*70)
    
    # Configurações
    glue_job_name = os.environ.get('GLUE_JOB_NAME')
    
    if not glue_job_name:
        raise ValueError("GLUE_JOB_NAME environment variable is required")
    
    # Processar evento S3
    try:
        for record in event['Records']:
            # Obter informações do objeto S3
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']
            
            logger.info(f"New object detected: s3://{bucket}/{key}")
            
            # Verificar se está no path raw/
            if not key.startswith('raw/'):
                logger.info(f"Skipping: object not in raw/ path")
                continue
            
            # Iniciar Glue Job
            response = glue_client.start_job_run(
                JobName=glue_job_name,
                Arguments={
                    '--S3_BUCKET': bucket,
                    '--S3_KEY': key,
                    '--EXECUTION_TIME': datetime.now().isoformat()
                }
            )
            
            job_run_id = response['JobRunId']
            
            logger.info(f"✅ Glue Job started successfully!")
            logger.info(f"   Job Name: {glue_job_name}")
            logger.info(f"   Job Run ID: {job_run_id}")
            logger.info(f"   Trigger: s3://{bucket}/{key}")
        
        logger.info("="*70)
        logger.info("LAMBDA TRIGGER GLUE - CONCLUÍDO")
        logger.info("="*70)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Glue job triggered successfully',
                'job_run_id': job_run_id
            })
        }
        
    except Exception as e:
        logger.error(f"ERROR: {str(e)}", exc_info=True)
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Error triggering Glue job',
                'error': str(e)
            })
        }
