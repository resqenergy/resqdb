"""Module to import datapacakges from S3."""

import shutil
import sys

from minio import Minio

from settings import (
    S3_ENDPOINT,
    S3_ACCESS_KEY,
    S3_SECRET_KEY,
    DATAPACKAGE_DIR,
)


def import_datapackage_from_s3(dp_name: str, *, force: bool = False) -> None:
    """Import datapackage from S3."""
    if (DATAPACKAGE_DIR / dp_name).exists():
        if force:
            shutil.rmtree(DATAPACKAGE_DIR / dp_name)
        else:
            raise FileExistsError(f"Datapackage '{dp_name}' already exists.")

    client = Minio(
        S3_ENDPOINT,
        access_key=S3_ACCESS_KEY,
        secret_key=S3_SECRET_KEY,
        secure=False,
    )

    prefix = f"datapackages/{dp_name}/"
    for item in client.list_objects("resq", prefix=prefix, recursive=True):
        relative_path = item.object_name.removeprefix(prefix)
        target_path = DATAPACKAGE_DIR / dp_name / relative_path
        client.fget_object("resq", item.object_name, target_path)


if __name__ == "__main__":
    force = sys.argv[1] == "--force" if len(sys.argv) > 1 else False
    import_datapackage_from_s3("adlershof_2035_mean_rcp85", force=force)
