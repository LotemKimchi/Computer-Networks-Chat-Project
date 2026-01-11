import socket
import threading

HOST = "127.0.0.1"
PORT = 5000


def recv_loop(sock: socket.socket):
    f = sock.makefile("r", encoding="utf-8", newline="\n")
    try:
        for line in f:
            print(line.strip())
    except Exception:
        pass


def send_line(sock: socket.socket, text: str):
    sock.sendall((text + "\n").encode("utf-8"))


def main():
    name = input("Enter your name: ").strip()
    if not name:
        print("Name is required")
        return

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))

    t = threading.Thread(target=recv_loop, args=(sock,), daemon=True)
    t.start()

    send_line(sock, f"HELLO {name}")

    print("Commands:")
    print("  /chat <name>  - start chat")
    print("  /end          - end chat")
    print("  /quit         - quit")
    print("Or type message text to send to your chat partner.")

    try:
        while True:
            msg = input("> ").strip()
            if not msg:
                continue

            if msg.startswith("/chat "):
                target = msg.split(" ", 1)[1]
                send_line(sock, f"CHAT {target}")
            elif msg == "/end":
                send_line(sock, "END")
            elif msg == "/quit":
                send_line(sock, "QUIT")
                break
            else:
                send_line(sock, f"MSG {msg}")

    finally:
        try:
            sock.close()
        except OSError:
            pass


if __name__ == "__main__":
    main()
