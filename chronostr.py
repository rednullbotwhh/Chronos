import socket
import requests
from concurrent.futures import ThreadPoolExecutor

def get_ip_properties(ip):
    ip_properties = {
        "IP Adresi": ip,
        "IP Versiyonu": "IPv4" if ":" not in ip else "IPv6",
    }

    try:
        hostname = socket.gethostbyaddr(ip)
        ip_properties["DNS Adı"] = hostname[0]
    except socket.herror:
        ip_properties["DNS Adı"] = "No_DNS_Entry"

    try:
        response = requests.get(f"https://ipinfo.io/{ip}/json")
        if response.status_code == 200:
            data = response.json()
            ip_properties["Sistem Adı"] = data.get("hostname", "Mevcut Değil")
            ip_properties["Ağ Arayüzü Adı"] = data.get("org", "Mevcut Değil")
            ip_properties["Konum"] = data.get("loc", "Mevcut Değil")
        else:
            print(f"IPinfo'dan veri alınırken hata oluştu: {response.status_code}")
    except Exception as e:
        print(f"Hata: {e}")

    return ip_properties

def scan_tcp_port(ip, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        try:
            s.connect((ip, port))
            return port, True
        except (socket.timeout, ConnectionRefusedError):
            return port, False

def scan_udp_port(ip, port):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(1)
        try:
            s.sendto(b'', (ip, port))
            s.recvfrom(1024)
            return port, True
        except socket.timeout:
            return port, False

def scan_ports(ip, start_port, end_port, turbo, protocol='tcp'):
    scan_function = scan_tcp_port if protocol == 'tcp' else scan_udp_port
    with ThreadPoolExecutor(max_workers=turbo) as executor:
        results = executor.map(lambda p: scan_function(ip, p), range(start_port, end_port + 1))
    return {port: status for port, status in results}

def scan_proxy_ports(ip, proxy_ports, turbo, protocol='tcp'):
    with ThreadPoolExecutor(max_workers=turbo) as executor:
        results = executor.map(lambda p: scan_tcp_port(ip, p) if protocol == 'tcp' else scan_udp_port(ip, p), proxy_ports)
    return {port: status for port, status in results}

server = input("Lütfen Sunucu IP'sini veya URL'sini giriniz: ")
port = int(input("Lütfen Portu giriniz (varsayılan 80): ") or 80)
start_port = int(input("Tarama için başlangıç portunu giriniz (varsayılan 1): ") or 1)
end_port = int(input("Tarama için bitiş portunu giriniz (varsayılan 1024): ") or 1024)
turbo = int(input("Turbo seviyesini giriniz (varsayılan 10): ") or 10)
silent_mode = input("Sessiz modu etkinleştirmek ister misiniz? (e/h): ").strip().lower() == 'e'
protocol = input("Tarama yapılacak protokolü seçiniz (tcp/udp): ").strip().lower() or 'tcp'

if not silent_mode:
    print(f"\n[Sunucu IP/URL: {server}]  [Port: {port}]  [Turbo: {turbo}]  [Protokol: {protocol}]\n")
    print("IP özellikleri alınıyor...\n")

ip_properties = get_ip_properties(server)
if not silent_mode:
    for key, value in ip_properties.items():
        print(f"{key}: {value}")

if not silent_mode:
    print(f"\n{start_port}-{end_port} portları taranıyor...\n")

found_open_port = False

scan_results = scan_ports(server, start_port, end_port, turbo, protocol)

normal_scan_results = {port: status for port, status in scan_results.items()}

proxy_ports = [8080, 3128, 8888, 1080, 8000]
if not silent_mode:
    print(f"\nProxy portları {proxy_ports} taranıyor...\n")

proxy_scan_results = scan_proxy_ports(server, proxy_ports, turbo, protocol)

all_results = {**normal_scan_results, **proxy_scan_results}

if not silent_mode:
    print("\nPort tarama sonuçları:")
    for port, is_open in all_results.items():
        if is_open:
            print(f"Port {port}: AÇIK")
        else:
            print(f"Port {port}: KAPALI")