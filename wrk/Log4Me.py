import os
import time
import logging
from datetime import date

class Log4Me:
    """
    A utility class for logging management and maintenance.

    The Log4Me class provides functions to initialize logging configuration,
    manage log files, and perform log-related tasks.

    Args:
        None

    Methods:
        self_exit(err_msg): Log an error message and exit the program.
        remove_old_logs(file_path, days_to_keep): Remove old log files from a directory.
        init_logging(log_name='LOG', log_days_to_keep=30, subdirectory='LOGS', asterisk_count=100):
            Initialize logging configuration and manage log files.
    """
    @staticmethod
    def self_exit(err_msg):
        """
        Log the error message and exit the program.

        :param err_msg: The error message to log and display.
        """
        logging.error(err_msg)
        print(err_msg)
        exit()

    @staticmethod
    def remove_old_logs(file_path, days_to_keep):
        """
        Remove log files older than a specified number of days.

        :param file_path: The path to the directory containing log files.
        :param days_to_keep: The number of days to keep log files.
        """
        now = time.time()
        try:
            for file in os.listdir(file_path):
                full_path = os.path.join(file_path, file)
                if os.path.isfile(full_path):
                    age_in_days = (now - os.path.getmtime(full_path)) / 86400
                    if age_in_days > days_to_keep:
                        os.remove(full_path)
        except Exception as e:
            raise Exception(e)

    @staticmethod
    def init_logging(log_name: str = 'LOG', log_days_to_keep: int = 30, subdirectory: str = 'LOGS', asterisk_count: int = 100, log_to_file: bool = False, log_level: logging = logging.INFO):
        """
        Initialize logging configuration and manage log files.

        :param log_to_file: False to log with standard output; True is save logs in file.
        :param log_name: The base name for log files (default: 'LOG').
        :param log_days_to_keep: The number of days to keep log files (default: 30).
        :param subdirectory: The subdirectory for log files (default: 'LOGS').
        :param asterisk_count: The number of asterisks for log separation (default: 100).
        :param log_level: Set logging level (default: INFO).

        Args:
            log_level:
        """
        today = date.today()
        log_path = ''
        subdirectory = subdirectory[1:] if subdirectory.startswith('/') else subdirectory
        log_format = '%(asctime)s %(levelname)s: %(message)s'

        print('[Log4Me] Initialization...')

        try:
            if log_to_file:
                if not os.path.exists(subdirectory):
                    os.makedirs(subdirectory)
                    print(f"[Log4Me] Created '{subdirectory}' subdirectory for logs")

                log_path = os.path.join(subdirectory, f'{log_name}_{today.strftime("%Y%m%d")}.log')
                log_path = os.path.abspath(log_path)
                full_path = os.path.dirname(log_path)

                print(f"[Log4Me] Path:  {log_path}")
                print(f"[Log4Me] Remove logs older than '{log_days_to_keep}' days under '{full_path}'")
                Log4Me.remove_old_logs(full_path, log_days_to_keep)

                # Configure logging to write to the log file
                logging.basicConfig(level=log_level, filename=log_path, filemode='a', format=log_format)
            else:
                logging.basicConfig(level=log_level, format='%(asctime)s %(levelname)s: %(message)s')

            logging.info('*' * asterisk_count)
            logging.info(f'[Log4Me] Logging Start: {log_path}' if log_to_file else f'[Log4Me] Logging Start...')

        except Exception as e:
            raise Exception(f"An error occurred during initialization: {e}")

if __name__ == "__main__":
    print("\033[31mLog sample 1\033[0m")
    log_sample_one = Log4Me()
    log_sample_one.init_logging()
    print("\n\n\033[31mLog sample 2\033[0m")
    log_sample_two = Log4Me()
    log_sample_two.init_logging(log_to_file=True)