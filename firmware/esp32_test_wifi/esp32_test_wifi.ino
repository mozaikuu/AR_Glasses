/**
 * Smart Glasses ESP32 - Full Pipeline Test
 * Works with phone file upload (bypasses browser camera/mic issues)
 */

#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <HTTPClient.h>

// ============== CONFIG ==============
const char *AP_SSID = "SmartGlasses_Test";
const char *AP_PASSWORD = "12345678";
const IPAddress AP_IP(192, 168, 4, 1);
const IPAddress AP_GATEWAY(192, 168, 4, 1);
const IPAddress AP_SUBNET(255, 255, 255, 0);

const char *WIFI_SSID = "Moussa24";
const char *WIFI_PASSWORD = "AhmedMoussa2003!";
const char *SERVER_URL = "http://192.168.100.2:8000/esp/process";

#define LED_PIN 2

// ============== STATE ==============
WebServer server(80);
bool serverConnected = false;

// ============== HTML - With file upload ==============
const char INDEX_HTML[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Smart Glasses Test</title>
<style>
body{font-family:Arial;background:#1a1a2e;color:#fff;padding:20px;text-align:center}
h1{color:#00d4ff}
.btn{background:#00d4ff;color:#000;padding:15px 25px;border:0;border-radius:8px;font-size:16px;margin:10px}
#out{background:#000;padding:10px;margin:10px 0;text-align:left;white-space:pre-wrap;height:200px;overflow:auto}
input[type=text]{width:70%;padding:10px;margin:5px}
input[type=file]{margin:10px}
</style>
</head>
<body>
<h1>Smart Glasses Test</h1>
<p>Server: <span id="srv">?</span></p>

<div>
<h3>1. Upload Audio</h3>
<input type="file" id="audioFile" accept="audio/*">
<button class="btn" onclick="uploadAudio()">Send Audio</button>
</div>

<div>
<h3>2. Upload Image</h3>
<input type="file" id="imageFile" accept="image/*">
<button class="btn" onclick="uploadImage()">Send Image</button>
</div>

<div>
<h3>3. Text Command</h3>
<input type="text" id="cmd" placeholder="Type message...">
<button class="btn" onclick="sendText()">Send</button>
</div>

<div id="out"></div>

<script>
var ESP = 'http://192.168.4.1';

function log(s){
  document.getElementById('out').innerHTML += s + '\n';
  document.getElementById('out').scrollTop = document.getElementById('out').scrollHeight;
}

async function uploadAudio(){
  var f = document.getElementById('audioFile').files[0];
  if(!f){log('Select an audio file first');return;}
  log('Reading audio file...');
  
  var reader = new FileReader();
  reader.onload = async function(){
    var base64 = reader.result.split(',')[1];
    log('Sending to server...');
    try{
      var r = await fetch(ESP+'/process', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({audio:base64, mode:'quick'})
      });
      var resp = await r.text();
      log('Server: '+resp);
    }catch(e){log('Error: '+e.message);}
  };
  reader.readAsDataURL(f);
}

async function uploadImage(){
  var f = document.getElementById('imageFile').files[0];
  if(!f){log('Select an image file first');return;}
  log('Reading image file...');
  
  var reader = new FileReader();
  reader.onload = async function(){
    var base64 = reader.result.split(',')[1];
    log('Sending to server...');
    try{
      var r = await fetch(ESP+'/process', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({image:base64, mode:'quick'})
      });
      var resp = await r.text();
      log('Server: '+resp);
    }catch(e){log('Error: '+e.message);}
  };
  reader.readAsDataURL(f);
}

async function sendText(){
  var txt = document.getElementById('cmd').value;
  if(!txt){log('Enter some text');return;}
  log('Sending: '+txt);
  try{
    var r = await fetch(ESP+'/process', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({text:txt, mode:'quick'})
    });
    var resp = await r.text();
    log('Server: '+resp);
  }catch(e){log('Error: '+e.message);}
}

setInterval(async function(){
  try{
    var j = await fetch(ESP+'/status').then(r=>r.json());
    document.getElementById('srv').innerText = j.server?'OK':'NO';
  }catch(e){document.getElementById('srv').innerText='ERR';}
},2000);

log('Ready. Select a file and click Send.');
</script>
</body>
</html>
)rawliteral";

// ============== WIFI ==============
void connectToWiFi()
{
  Serial.println("Connecting to WiFi...");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20)
  {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  if (WiFi.status() == WL_CONNECTED)
  {
    Serial.println("\nWiFi connected!");
    serverConnected = true;
  }
  else
  {
    Serial.println("\nWiFi failed!");
    serverConnected = false;
  }
}

// ============== HANDLERS ==============
void handleRoot()
{
  server.send(200, "text/html; charset=utf-8", INDEX_HTML);
}

void handleStatus()
{
  String json = "{\"status\":\"ok\",\"server\":" + String(serverConnected ? "true" : "false") + "}";
  server.send(200, "application/json", json);
}

void handleProcess()
{
  if (server.hasArg("plain"))
  {
    String body = server.arg("plain");
    Serial.println("Forwarding to server...");

    if (WiFi.status() != WL_CONNECTED)
      connectToWiFi();

    HTTPClient http;
    http.begin(String(SERVER_URL));
    http.addHeader("Content-Type", "application/json");

    int code = http.POST(body);
    String resp = (code == 200) ? http.getString() : "{\"response\":\"ERROR\"}";
    http.end();

    Serial.println("Response: " + resp);
    digitalWrite(LED_PIN, !digitalRead(LED_PIN));
    server.send(200, "application/json", resp);
  }
  else
  {
    server.send(400, "text/plain", "No data");
  }
}

void handleNotFound()
{
  server.send(404, "text/plain", "Not Found");
}

// ============== SETUP ==============
void setup()
{
  Serial.begin(115200);
  Serial.println("\n=== Smart Glasses ===");
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  WiFi.mode(WIFI_AP_STA);
  WiFi.softAPConfig(AP_IP, AP_GATEWAY, AP_SUBNET);
  WiFi.softAP(AP_SSID, AP_PASSWORD);
  Serial.println("AP: " + String(AP_SSID) + " IP: 192.168.4.1");

  connectToWiFi();

  server.on("/", handleRoot);
  server.on("/status", handleStatus);
  server.on("/process", HTTP_POST, handleProcess);
  server.onNotFound(handleNotFound);
  server.begin();
  Serial.println("Server started");
}

// ============== LOOP ==============
void loop()
{
  server.handleClient();
  static unsigned long last = 0;
  if (millis() - last > 1000)
  {
    last = millis();
    digitalWrite(LED_PIN, !digitalRead(LED_PIN));
  }
}
