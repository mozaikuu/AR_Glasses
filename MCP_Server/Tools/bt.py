# Simple Bluetooth RFCOMM server that accepts a single connection,
# then sends a one-line "ip:port" message so Android clients can find the TCP endpoint.
import threading
import socket
import bluetooth  # pybluez

def start_bt_broadcast(server_ip, server_port, name="SmartGlassesMCP"):
    """
    Starts a background thread that listens for incoming bluetooth RFCOMM connections.
    When a client connects, it will send a single line: "ip:port\n" and close.
    This allows Android to discover the server IP:port via Bluetooth.
    """
    server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    server_sock.bind(("", bluetooth.PORT_ANY))
    server_sock.listen(1)
    bt_port = server_sock.getsockname()[1]

    # advertise SPP / custom service
    uuid = "00001101-0000-1000-8000-00805F9B34FB"
    bluetooth.advertise_service(
        server_sock,
        name,
        service_id=uuid,
        service_classes=[uuid, bluetooth.SERIAL_PORT_CLASS],
        profiles=[bluetooth.SERIAL_PORT_PROFILE],
        description="Smart Glasses MCP Bluetooth helper"
    )

    def accept_loop():
        print(f"[BT] RFCOMM listening on port {bt_port}. Waiting for Android to connect...")
        while True:
            try:
                client_sock, client_info = server_sock.accept()
                print("[BT] Client connected:", client_info)
                try:
                    # send the tcp endpoint as a simple line
                    payload = f"{server_ip}:{server_port}\n"
                    client_sock.send(payload.encode("utf-8"))
                    print("[BT] Sent endpoint to client:", payload.strip())
                except Exception as e:
                    print("BT send error:", e)
                finally:
                    client_sock.close()
            except Exception as e:
                print("BT accept error:", e)
                break

    thr = threading.Thread(target=accept_loop, daemon=True)
    thr.start()
    return server_sock
