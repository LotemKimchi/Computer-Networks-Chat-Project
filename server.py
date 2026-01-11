import socket
import threading

HOST = "127.0.0.1"
PORT = 5000

clients = {}   # name -> socket
partners = {}  # name -> partner name or None
lock = threading.Lock()


def send_line(conn: socket.socket, text: str):
    try:
        conn.sendall((text + "\n").encode("utf-8"))
    except OSError:
        pass


def cleanup_user(name: str | None):
    if not name:
        return

    with lock:
        partner = partners.get(name)
        clients.pop(name, None)
        partners.pop(name, None)

        # if user had a partner, detach the partner too
        if partner and partner in partners:
            partners[partner] = None
            pconn = clients.get(partner)
            if pconn:
                send_line(pconn, f"INFO {name} disconnected. Chat ended.")


def handle_client(conn: socket.socket, addr):
    name = None
    send_line(conn, "INFO Welcome! Please login: HELLO <name>")

    try:
        f = conn.makefile("r", encoding="utf-8", newline="\n")

        for raw in f:
            line = raw.strip()
            if not line:
                continue

            parts = line.split(" ", 1)
            cmd = parts[0].upper()
            payload = parts[1] if len(parts) > 1 else ""

            if cmd == "HELLO":
                desired = payload.strip()
                if not desired:
                    send_line(conn, "ERR Missing name. Usage: HELLO <name>")
                    continue

                with lock:
                    if desired in clients:
                        send_line(conn, "ERR Name already taken")
                        continue
                    name = desired
                    clients[name] = conn
                    partners[name] = None

                send_line(conn, f"OK Logged in as {name}")
                continue

            # Must be logged in for everything else
            if not name:
                send_line(conn, "ERR You must login first: HELLO <name>")
                continue

            if cmd == "CHAT":
                target = payload.strip()
                if not target:
                    send_line(conn, "ERR Usage: CHAT <target>")
                    continue

                with lock:
                    if target not in clients:
                        send_line(conn, "ERR User not found")
                        continue
                    if target == name:
                        send_line(conn, "ERR Cannot chat with yourself")
                        continue
                    if partners.get(name) is not None:
                        send_line(conn, "ERR You are already in a chat. Use END first.")
                        continue
                    if partners.get(target) is not None:
                        send_line(conn, f"ERR {target} is already in a chat")
                        continue

                    partners[name] = target
                    partners[target] = name
                    target_conn = clients.get(target)

                send_line(conn, f"OK Chat started with {target}")
                if target_conn:
                    send_line(target_conn, f"INFO {name} started a chat with you")
                continue

            if cmd == "MSG":
                text = payload
                if not text:
                    send_line(conn, "ERR Usage: MSG <text>")
                    continue

                with lock:
                    partner = partners.get(name)
                    partner_conn = clients.get(partner) if partner else None

                if not partner or not partner_conn:
                    send_line(conn, "ERR No active chat. Use CHAT <name> first.")
                    continue

                send_line(partner_conn, f"FROM {name} {text}")
                send_line(conn, "OK sent")
                continue

            if cmd == "END":
                with lock:
                    partner = partners.get(name)
                    if not partner:
                        send_line(conn, "ERR No active chat")
                        continue
                    partners[name] = None
                    if partner in partners:
                        partners[partner] = None
                    partner_conn = clients.get(partner)

                send_line(conn, "OK Chat ended")
                if partner_conn:
                    send_line(partner_conn, f"INFO {name} ended the chat")
                continue

            if cmd == "QUIT":
                send_line(conn, "OK Bye")
                break

            send_line(conn, f"ERR Unknown command: {cmd}")

    except Exception:
        pass
    finally:
        cleanup_user(name)
        try:
            conn.close()
        except OSError:
            pass
        print(f"[DISCONNECT] {addr} user={name}")


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[SERVER] Listening on {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        print(f"[CONNECT] {addr}")
        t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
        t.start()


if __name__ == "__main__":
    main()
