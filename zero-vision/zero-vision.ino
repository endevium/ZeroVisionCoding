/*
  BRAILLE KEYBOARD PRO VERSION (THESIS READY)
  Arduino Pro Micro / Micro
  Stable + Debounced + Smooth Typing
*/

#include <Keyboard.h>

// ==================== PIN DEFINITIONS ====================
const int DOT_PINS[8] = {2,3,4,5,6,7,8,9}; 
// dot1,2,3,7 (left) | dot4,5,6,8 (right)

const int SPACE_PIN = 16;   // SPACE
const int ENTER_PIN = 10;   // ENTER

const int FN_PIN   = A3;
const int BACK_PIN = A2;
const int TAB_PIN  = A0;
const int SYM_PIN  = A1;

const int LED_PIN = 17; // RX LED

// ==================== SETTINGS ====================
const unsigned long CHORD_TIMEOUT = 350;   // more friendly for blind users
const unsigned long DEBOUNCE = 35;         // debounce time

// ==================== STATE ====================
bool dotStates[8];
bool chordActive = false;
unsigned long chordStart = 0;

bool symbolMode = false;
bool fnMode = false;

// debounce states
unsigned long lastPressTime[20];

// ==================== SETUP ====================
void setup() {
  Keyboard.begin();
  Serial.begin(9600);

  for(int i=0;i<8;i++){
    pinMode(DOT_PINS[i], INPUT_PULLUP);
  }

  pinMode(SPACE_PIN, INPUT_PULLUP);
  pinMode(ENTER_PIN, INPUT_PULLUP);
  pinMode(FN_PIN, INPUT_PULLUP);
  pinMode(BACK_PIN, INPUT_PULLUP);
  pinMode(TAB_PIN, INPUT_PULLUP);
  pinMode(SYM_PIN, INPUT_PULLUP);

  pinMode(LED_PIN, OUTPUT);

  delay(1200); // safety startup delay

  // ready blink
  for(int i=0;i<3;i++){
    digitalWrite(LED_PIN,HIGH); delay(120);
    digitalWrite(LED_PIN,LOW); delay(120);
  }

  Serial.println("BRAILLE KEYBOARD READY");
}

// ==================== LOOP ====================
void loop(){
  handleFunctionKeys();
  handleBraille();
  delay(5);
}

// ==================== SAFE PRESS ====================
bool safePress(int pin){
  if(!digitalRead(pin)){
    if(millis() - lastPressTime[pin] > DEBOUNCE){
      lastPressTime[pin] = millis();
      return true;
    }
  }
  return false;
}

// ==================== FUNCTION KEYS ====================
void handleFunctionKeys(){

  if(!digitalRead(FN_PIN)) fnMode = true;
  else fnMode = false;

  // SPACE
  if(safePress(SPACE_PIN)){
    Keyboard.write(' ');
    flashLED(1);
    Serial.println("[SPACE]");
  }

  // ENTER
  if(safePress(ENTER_PIN)){
    Keyboard.write(KEY_RETURN);
    flashLED(1);
    Serial.println("[ENTER]");
  }

  // BACKSPACE
  if(safePress(BACK_PIN)){
    Keyboard.write(KEY_BACKSPACE);
    flashLED(2);
    Serial.println("[BACKSPACE]");
  }

  // TAB
  if(safePress(TAB_PIN)){
    Keyboard.write(KEY_TAB);
    flashLED(1);
    Serial.println("[TAB]");
  }

  // SYMBOL MODE TOGGLE
  if(safePress(SYM_PIN)){
    symbolMode = !symbolMode;
    flashLED(symbolMode ? 4 : 2);
    Serial.println(symbolMode ? "SYMBOL ON":"SYMBOL OFF");
  }
}

// ==================== BRAILLE HANDLING ====================
void handleBraille(){
  bool current[8];
  bool any=false;

  for(int i=0;i<8;i++){
    current[i] = !digitalRead(DOT_PINS[i]);
    if(current[i]) any=true;
  }

  // start chord
  if(any && !chordActive){
    chordActive=true;
    chordStart=millis();
    memset(dotStates,false,sizeof(dotStates));
    digitalWrite(LED_PIN,HIGH);
  }

  // record pressed dots
  if(chordActive){
    for(int i=0;i<8;i++){
      if(current[i]) dotStates[i]=true;
    }

    // release or timeout
    if(!any || millis()-chordStart > CHORD_TIMEOUT){
      processChord();
      chordActive=false;
      digitalWrite(LED_PIN,LOW);
    }
  }
}

// ==================== PROCESS ====================
void processChord(){
  byte pattern=0;

  for(int i=0;i<8;i++){
    if(dotStates[i]) pattern |= (1<<i);
  }

  if(pattern==0) return;

  char out=0;

  if(symbolMode) out = brailleSymbol(pattern);
  else out = brailleChar(pattern);

  if(out!=0){
    Keyboard.write(out);
    Serial.print(out);
    flashLED(1);
  }else{
    flashLED(5);
    Serial.print("?");
  }
}

// ==================== BRAILLE LETTER ====================
char brailleChar(byte p){
  byte base = p & 0x3F;
  bool cap = p & 0x40;
  bool num = p & 0x80;

  if(num){
    switch(base){
      case 1: return '1';
      case 3: return '2';
      case 9: return '3';
      case 25: return '4';
      case 17: return '5';
      case 11: return '6';
      case 27: return '7';
      case 19: return '8';
      case 10: return '9';
      case 26: return '0';
    }
  }

  char r=0;

  switch(base){
    case 1:r='a';break;
    case 3:r='b';break;
    case 9:r='c';break;
    case 25:r='d';break;
    case 17:r='e';break;
    case 11:r='f';break;
    case 27:r='g';break;
    case 19:r='h';break;
    case 10:r='i';break;
    case 26:r='j';break;
    case 5:r='k';break;
    case 7:r='l';break;
    case 13:r='m';break;
    case 29:r='n';break;
    case 21:r='o';break;
    case 15:r='p';break;
    case 31:r='q';break;
    case 23:r='r';break;
    case 14:r='s';break;
    case 30:r='t';break;
    case 37:r='u';break;
    case 39:r='v';break;
    case 58:r='w';break;
    case 45:r='x';break;
    case 61:r='y';break;
    case 53:r='z';break;
  }

  if(cap && r>='a' && r<='z') r -= 32;
  return r;
}

// ==================== SYMBOL ====================
char brailleSymbol(byte p){
  byte b = p & 0x3F;

  switch(b){

    // ===== STRINGS =====
    case 2:  return '"';
    case 4:  return '\'';
    case 6:  return '_';
    case 8:  return '.';
    case 24: return ',';
    case 16: return ':';
    case 48: return ';';

    // ===== BRACKETS =====
    case 18: return '(';
    case 34: return ')';
    case 20: return '[';
    case 36: return ']';
    case 40: return '{';
    case 56: return '}';

    // ===== OPERATORS =====
    case 38: return '+';
    case 42: return '-';
    case 44: return '*';
    case 50: return '/';
    case 52: return '=';
    case 46: return '%';

    // ===== LOGIC =====
    case 22: return '<';
    case 54: return '>';
    case 28: return '#';
  }

  return 0;
}
// ==================== LED ====================
void flashLED(int t){
  for(int i=0;i<t;i++){
    digitalWrite(LED_PIN,HIGH); delay(60);
    digitalWrite(LED_PIN,LOW); delay(60);
  }
}