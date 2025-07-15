import logging
from datetime import datetime


class FileTransferHistory:
    def __init__(self):
        self.transfers = []
        logging.basicConfig(filename="transfer_history.log", level=logging.INFO)

    def add_transfer(self, file_name, status):
        transfer_record = f"{datetime.now()}: {file_name} - {status}"
        self.transfers.append(transfer_record)
        logging.info(transfer_record)

    def get_history(self):
        return "\n".join(self.transfers)
