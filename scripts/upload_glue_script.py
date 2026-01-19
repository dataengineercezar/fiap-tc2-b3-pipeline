import boto3


def main() -> None:
    s3 = boto3.client("s3")

    bucket = "pos-tech-b3-pipeline-cezar-2026"
    key = "glue/scripts/glue_etl_job.py"
    file_path = "src/glue/glue_etl_job.py"

    print(f"Fazendo upload de {file_path} para s3://{bucket}/{key}...")
    s3.upload_file(file_path, bucket, key)
    print("✅ Upload concluído!")


if __name__ == "__main__":
    main()
