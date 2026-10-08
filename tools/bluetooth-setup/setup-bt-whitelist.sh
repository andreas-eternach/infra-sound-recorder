#!/bin/bash

# Farben für die Ausgabe
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Bitte starte das Skript als root (sudo ./setup-bt-whitelist.sh)${NC}"
  exit 1
fi

echo -e "${BLUE}=== Starte Einrichtung des Bluetooth-Webserver-Zugangs mit WHITELISTING ===${NC}"

# 1. Pakete installieren
echo -e "\n${BLUE}[1/5] Installiere notwendige Pakete...${NC}"
apt update && apt upgrade -y
apt install pi-bluetooth bluez python3-dbus network-manager -y

# 2. NetworkManager Bluetooth-PAN (NAP) erstellen
echo -e "\n${BLUE}[2/5] Konfiguriere NetworkManager (Bluetooth PAN/NAP)...${NC}"
nmcli connection delete "BT-Webserver-Netz" 2>/dev/null
nmcli connection add type bluetooth con-name "BT-Webserver-Netz" ifname bt-pan bluetooth.type nap ipv4.method shared
nmcli connection modify "BT-Webserver-Netz" connection.autoconnect yes
nmcli connection modify "BT-Webserver-Netz" connection.autoconnect-priority 100

# 3. Bluetooth-Sichtbarkeit einstellen
echo -e "\n${BLUE}[3/5] Passe Bluetooth-Systemkonfiguration an...${NC}"
BT_CONF="/etc/bluetooth/main.conf"
sed -i 's/^#\?DiscoverableTimeout.*/DiscoverableTimeout = 0/' $BT_CONF
sed -i 's/^#\?PairableTimeout.*/PairableTimeout = 0/' $BT_CONF
sed -i 's/^#\?AutoConnectTimeout.*/AutoConnectTimeout = 0/' $BT_CONF
if grep -q "AutoEnable" $BT_CONF; then
    sed -i 's/^#\?AutoEnable.*/AutoEnable=true/' $BT_CONF
else
    if grep -q "\[Policy\]" $BT_CONF; then
        sed -i '/\[Policy\]/a AutoEnable=true' $BT_CONF
    else
        echo -e "\n[Policy]\nAutoEnable=true" >> $BT_CONF
    fi
fi
rfkill unblock bluetooth
systemctl restart bluetooth

# 4. Whitelist-Datei erstellen, falls nicht vorhanden
if [ ! -f /etc/bluetooth/whitelist.txt ]; then
    echo -e "\n${BLUE}[4/5] Erstelle leere Whitelist-Datei unter /etc/bluetooth/whitelist.txt...${NC}"
    touch /etc/bluetooth/whitelist.txt
    echo "# Trage hier erlaubte MAC-Adressen ein (z.B. AA:BB:CC:DD:EE:FF)" > /etc/bluetooth/whitelist.txt
fi

# 5. Python Whitelist-Agenten erstellen
echo -e "\n${BLUE}[5/5] Erstelle den intelligenten Python-Sicherheits-Agenten...${NC}"
AGENT_PATH="/usr/local/bin/bt_whitelist_agent.py"

cat << 'EOF' > $AGENT_PATH
#!/usr/bin/env python3
import sys
import dbus
import dbus.service
import dbus.mainloop.glib
from gi.repository import GLib

WHITELIST_FILE = "/etc/bluetooth/whitelist.txt"
AGENT_INTERFACE = "org.bluez.Agent1"

def is_whitelisted(address):
    try:
        with open(WHITELIST_FILE, "r") as f:
            allowed = [line.strip().upper() for line in f if line.strip() and not line.startswith("#")]
        return address.upper() in allowed
    except Exception:
        return False

class WhitelistAgent(dbus.service.Object):
    @dbus.service.method(AGENT_INTERFACE, in_signature="ou", out_signature="")
    def RequestPinCode(self, device, timeout):
        raise dbus.exceptions.DBusException("org.bluez.Error.Rejected")

    @dbus.service.method(AGENT_INTERFACE, in_signature="o", out_signature="s")
    def RequestPasskey(self, device):
        raise dbus.exceptions.DBusException("org.bluez.Error.Rejected")

    @dbus.service.method(AGENT_INTERFACE, in_signature="ou", out_signature="")
    def DisplayPasskey(self, device, passkey):
        pass

    @dbus.service.method(AGENT_INTERFACE, in_signature="os", out_signature="")
    def RequestConfirmation(self, device, passkey):
        # Bluetooth-Objektpfade sehen so aus: /org/bluez/hci0/dev_AA_BB_CC_DD_EE_FF
        address = device.split("dev_")[1].replace("_", ":")
        if is_whitelisted(address):
            print(f"[ERLAUBT] Verbindung von Whitelist-Gerät akzeptiert: {address}")
            return
        else:
            print(f"[REJECTED] Unbekanntes Gerät blockiert: {address}")
            raise dbus.exceptions.DBusException("org.bluez.Error.Rejected")

    @dbus.service.method(AGENT_INTERFACE, in_signature="o", out_signature="")
    def AuthorizeService(self, device, uuid):
        address = device.split("dev_")[1].replace("_", ":")
        if is_whitelisted(address):
            return
        raise dbus.exceptions.DBusException("org.bluez.Error.Rejected")

    @dbus.service.method(AGENT_INTERFACE, in_signature="", out_signature="")
    def Cancel(self):
        pass

if __name__ == "__main__":
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()
    
    agent = WhitelistAgent(bus, "/test/agent")
    obj = bus.get_object("org.bluez", "/org/bluez")
    manager = dbus.Interface(obj, "org.bluez.AgentManager1")
    
    manager.RegisterAgent("/test/agent", "NoInputNoOutput")
    manager.RequestDefaultAgent("/test/agent")
    
    print("Bluetooth Whitelist-Agent läuft und sichert das System...")
    mainloop = GLib.MainLoop()
    mainloop.run()
EOF

chmod +x $AGENT_PATH

# 6. Systemd-Service für den Python-Agenten einrichten
SERVICE_FILE="/etc/systemd/system/bt-whitelist-agent.service"
# Alten bt-agent Service stoppen und entfernen falls vorhanden
systemctl stop bt-agent.service 2>/dev/null
systemctl disable bt-agent.service 2>/dev/null

cat << EOF > $SERVICE_FILE
[Unit]
Description=Bluetooth Whitelist Auth Agent
After=bluetooth.service
Requires=bluetooth.service

[Service]
ExecStart=$AGENT_PATH
Restart=always
StandardOutput=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable bt-whitelist-agent.service
systemctl start bt-whitelist-agent.service

echo -e "\n${GREEN}================================================================${NC}"
echo -e "${GREEN} Whitelist-Einrichtung erfolgreich abgeschlossen!${NC}"
echo -e "${GREEN}================================================================${NC}"
echo -e "Es werden NUR noch Geräte akzeptiert, deren MAC-Adresse in"
echo -e "${BLUE}/etc/bluetooth/whitelist.txt${NC} eingetragen ist."
echo -e "\nBitte starte den Pi neu, um alle Änderungen aktiv zu schalten: ${BLUE}sudo reboot${NC}"
echo -e "${GREEN}================================================================${NC}"
