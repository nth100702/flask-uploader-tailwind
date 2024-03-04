from models import User, SubmitRecord, FileUpload, ChunkedFile
from app import db, log
import requests, os
import shutil
import time


# database helpers
def get_user(query: dict):
    try:
        user = User.query.filter_by(**query).first()
        if user is None:
            user = User(**query)
            db.session.add(user)
            db.session.commit()
            log.info(f"Inserted user to db")
            user = User.query.filter_by(**query).first()
        return user
    except Exception as e:
        # Handle the exception here
        print(f"Error occurred in get_user: {str(e)}")
        return None


def get_submit_record(query: dict):
    try:
        submit_record = SubmitRecord.query.filter_by(**query).first()
        if submit_record is None:
            submit_record = SubmitRecord(**query)
            db.session.add(submit_record)
            db.session.commit()
            log.info(f"Inserted submit record to db")
            submit_record = SubmitRecord.query.filter_by(**query).first()
        return submit_record
    except Exception as e:
        # Handle the exception here
        print(f"Error occurred in get_submit_record: {str(e)}")
        return None


def get_file_upload(query: dict, new: bool = False):
    try:
        file_upload = FileUpload.query.filter_by(**query).first()
        if file_upload is None or new:
            file_upload = FileUpload(**query)
            db.session.add(file_upload)
            db.session.commit()
            log.info(f"Inserted file upload to db")
            file_upload = FileUpload.query.filter_by(**query).first()
        return file_upload
    except Exception as e:
        # Handle the exception here
        print(f"Error occurred in get_file_upload: {str(e)}")
        return None


def is_first_chunk(dzuuid):
    first_chunk = ChunkedFile.query.filter_by(dzuuid=dzuuid).first()
    return first_chunk is None


def add_chunked_file(**args):
    try:
        chunked_file = ChunkedFile(**args)
        db.session.add(chunked_file)
        db.session.commit()
        log.info(f"Inserted chunked file to db")
        return chunked_file
    except Exception as e:
        # Handle the exception here
        print(f"Error occurred in add_chunked_file: {str(e)}")
        return None


def file_exist_check(*args):
    filepath = os.path.join(*args)
    try:
        with open(filepath, "r"):
            return True
    except:
        return False


# files helpers
"""
Errors related to file writes should be handled in the main app (centrally)
  - since user input is involved, it's better to handle it in the main app
Database errors should be handled independently by each helper function
  - db errors => server problems, only the engineer could fix it (user !involved)
"""

"""Save_chunk
- Save the chunk to disk using standard pythonic way
- Implement retry mechanism to handle file write errors
- Handle file write errors in the main app
"""


def save_chunk(chunk_content, chunk_path):
    try:
        if chunk_content is None or chunk_path is None:
            raise ValueError("Chunk content or path is empty")

        with open(chunk_path, "wb") as f:
            f.write(chunk_content.read())
            log.info(f"Saved chunk to {chunk_path}")
    except:
        raise Exception(
            f"Oops! Critical error occurred while saving chunk to {chunk_path}!"
        )


"""retry()
- takes max_retries num & a function with its arguments as input
"""


def retry(max_retries: int, func, *args, **kwargs):
    # *args: pass any number of positional arguments
    # **kwargs: pass any number of keyword arguments
    retry_count = 0
    while retry_count < max_retries:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            log.error(f"Error occurred: {str(e)}")
            retry_count += 1
            log.warning(
                f"Request failed. Retrying... (Attempt {retry_count}/{max_retries})"
            )
            time.sleep(1)  # Wait for 1 second before retrying
    else:
        log.error(f"Max retries exceeded. Request failed.")
        raise Exception(
            "Uh oh! Server không thể lưu file upload này. Vui lòng refresh trang và thử lại!"
        )


def save_chunk_with_retry(chunk_content, chunk_path):
    return retry(3, save_chunk, chunk_content, chunk_path)


def reassemble_file(
    temp_dir: str, filename: str, dztotalchunkcount
):
    # output file path is one level up from the temp_dir
    output_filepath = os.path.join(temp_dir, "..", filename)
    print("output_filepath", output_filepath)

    def _get_chunks(
        dztotalchunkcount=dztotalchunkcount,
        temp_dir=temp_dir,
        filename=filename,
    ):
        """Returns a list of missing chunks if any"""
        chunks = []
        for i in range(dztotalchunkcount):
            filename_noextension = filename.split(".")[0]
            chunk_filename = f"{filename_noextension}_{i}.part"
            chunk_path = os.path.join(temp_dir, chunk_filename)
            # check if the chunk exists
            if not os.path.exists(chunk_path):
                return None  # Break out of the for loop if a chunk path is nonexistent
            else:
                chunks.append(chunk_path)
        return chunks

    def _clean_up(temp_dir=temp_dir):
        # force remove all chunks, ignore errors
        try:
            shutil.rmtree(temp_dir)
        except OSError:
            pass

    # Reassemble the file from the chunks
    with open(output_filepath, "wb") as output_file:
        chunks = _get_chunks(dztotalchunkcount, temp_dir, filename)
        if chunks is None:
            _clean_up()
            raise FileNotFoundError(f"Missing chunks for {filename}")
        # write chunks to the output file
        for chunk in chunks:
            with open(chunk, "rb") as chunk_file:
                output_file.write(chunk_file.read())
        # success log
        log.info(f"Successfully reassembled {chunk} to {output_filepath}")

    # check if the file has been reassembled
    if not file_exist_check(output_filepath):
        _clean_up()
        raise Exception(f"Oops! Critical error occurred while reassembling {filename}!")

    # clean up chunks
    _clean_up()
    return True


def ensure_file_integrity(file_path: str, file_size: int):
    # check if the file has been reassembled
    if not file_exist_check(file_path):
        raise FileNotFoundError(f"Oops! {file_path} is missing!")
    # check if the file size is correct
    if os.path.getsize(file_path) != file_size:
        raise ValueError(f"Oops! {file_path} is corrupted!")


def handle_corrupted_file():
    return ""


"""
TO-DO: feat/Concurrent file uploads using background tasks
- Use a task queue to handle concurrent (large) file uploads: Celery, https://flask.palletsprojects.com/en/latest/patterns/celery/

"""
