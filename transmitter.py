import argparse
import logging
import socket
from typing import List

import sys


def progress_bar(iteration, total, prefix="", suffix="", length=50, fill="█"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    """
    percent = ("{0:.1f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + "-" * (length - filled_length)
    sys.stdout.write(f"\r{prefix} |{bar}| {percent}% {suffix}")
    sys.stdout.flush()

    # Print a new line after completion
    if iteration == total:
        print()


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("transmitter.log"), logging.StreamHandler()],
)


def send_file(filename, ip, port):
    """
    Function to send a file over TCP socket.

    :param filename: Name of the file to send.
    :param ip: IP address of the receiver.
    :param port: Port number of the receiver.
    """
    # Read the file in chunks and store in FILE
    logging.debug(f"Sending file: {filename} to {ip}:{port}")
    try:
        FILE: List[bytes] = []
        with open(filename, "rb") as file:
            # Read the file in chunks and append to FILE
            while chunk := file.read(4096):
                FILE.append(chunk)
        FILE_SIZE: int = len(FILE) * 4096
    except FileNotFoundError:
        logging.error(f"File not found: {filename}")
        return
    except Exception as e:
        logging.error(f"Error reading file: {e}")
        return
    logging.debug(f"File size: {FILE_SIZE} bytes")

    # Listen on the specified IP and port
    logging.debug(f"Listening on {ip}:{port}")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((ip, port))
        sock.listen(1)
    except socket.error as e:
        logging.error(f"Socket error: {e}")
        return
    except KeyboardInterrupt:
        logging.info("Program interrupted by user.")
        return
    except Exception as e:
        logging.error(f"Error binding socket: {e}")
        return

    while True:  # Exit on keyboardinterrupt
        logging.debug("Waiting for connection...")
        conn, addr = sock.accept()
        logging.debug(f"Connection established with {addr}")
        try:
            # Send the file size first
            conn.sendall(str(FILE_SIZE).encode())
            # Send the file chunks
            for chunk in FILE:
                conn.sendall(chunk)
            logging.debug("File sent successfully.")
        except Exception as e:
            logging.error(f"Error sending file: {e}")
        finally:
            conn.close()
            logging.debug("Connection closed.")


def receive_file(filename, ip, port):
    """
    Function to receive a file over TCP socket.

    :param ip: IP address to bind to.
    :param port: Port number to bind to.
    """
    # Listen on the specified IP and port
    logging.debug(f"Receiving file on {ip}:{port}")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ip, port))
    except socket.error as e:
        logging.error(f"Socket error: {e}")
        return
    except KeyboardInterrupt:
        logging.info("Program interrupted by user.")
        return
    except Exception as e:
        logging.error(f"Error binding socket: {e}")
        return

    while True:
        try:
            # Receive the file size first
            file_size = sock.recv(1024).decode()
            if not file_size:
                break
            file_size = int(file_size)
            logging.debug(f"File size: {file_size} bytes")

            # Receive the file chunks
            with open(filename, "wb") as file:
                received_bytes = 0
                while received_bytes < file_size:
                    progress_bar(
                        received_bytes,
                        file_size,
                        prefix="Progress:",
                        suffix="Complete",
                        length=50,
                    )
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    file.write(chunk)
                    received_bytes += len(chunk)
                    logging.debug(f"Received {received_bytes} bytes")
            logging.debug("File received successfully.")
            progress_bar(
                file_size,
                file_size,
                prefix="Progress:",
                suffix="Complete",
                length=50,
            )
        except Exception as e:
            logging.error(f"Error receiving file: {e}")
        finally:
            sock.close()
            logging.debug("Connection closed.")
            break
    logging.debug("Exiting receiver.")


def main():
    parser = argparse.ArgumentParser(
        description="Transmitter program for sending and receiving files over TCP sockets."
    )
    # Logging level argument
    parser.add_argument(
        "-l",
        "--log-level",
        type=str,
        default="DEBUG",
        help="Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    send_parser = subparsers.add_parser("send")
    send_parser.add_argument("filename", type=str, help="The name of the file to send.")
    send_parser.add_argument("ip", type=str, help="The IP address of the receiver.")
    send_parser.add_argument("port", type=int, help="The port number of the receiver.")

    recv_parser = subparsers.add_parser("recv")
    recv_parser.add_argument(
        "filename",
        type=str,
        help="The name of the file to save.",
        default="received_file",
    )
    recv_parser.add_argument("ip", type=str, help="The IP address to bind to.")
    recv_parser.add_argument("port", type=int, help="The port number to bind to.")

    args = parser.parse_args()

    # Set the logging level based on the command line argument
    logging.getLogger().setLevel(args.log_level.upper())

    if args.command == "send":
        # Call the send function with the provided arguments
        send_file(args.filename, args.ip, args.port)
    elif args.command == "recv":
        # Call the receive function with the provided arguments
        receive_file(args.filename, args.ip, args.port)
    else:
        parser.print_help()
        exit(1)


if __name__ == "__main__":
    main()
