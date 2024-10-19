#include <TimerOne.h>
#include <LiquidCrystal.h>

LiquidCrystal lcd(13, 12, 11, 10, 9, 8);

const int heartBeatSensorPin = 4; // Sensor Pin
const int startButtonPin = 2;  // Pushbutton Pin

volatile int heartBeatCount = 0;
volatile int elapsedSeconds = 0;
int heartBeatsPerMinute = 0;
bool isCounting = false;
bool isPulseHigh = false;

void setup() {
  pinMode(heartBeatSensorPin, INPUT);
  pinMode(startButtonPin, INPUT_PULLUP);

  Timer1.initialize(1000000); // 1 second interval
  Timer1.attachInterrupt(timerIsr);

  lcd.begin(20, 4); // Set up the LCD's number of columns and rows
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("         APSR    ");
  lcd.setCursor(0, 1);
  lcd.print("  Heart-Beat  Sensor  ");
  lcd.setCursor(0, 3);
  lcd.print("    Press Button");

  Serial.begin(9600);
}

void loop() {
  if (digitalRead(startButtonPin) == LOW && !isCounting) {
    delay(50); // Debounce delay
    if (digitalRead(startButtonPin) == LOW) {
      lcd.setCursor(0, 2);
      lcd.print(" HB Counting... ");
      lcd.setCursor(0, 3);
      lcd.print(" Please Wait: ");
      isCounting = true;
    }
  }

  if (isCounting) {
    if (digitalRead(heartBeatSensorPin) == HIGH && !isPulseHigh) {
      heartBeatCount++;
      isPulseHigh = true;
      lcd.setCursor(0, 2);
      lcd.print(" High Pulse ");
      lcd.print(heartBeatCount);
    } else if (digitalRead(heartBeatSensorPin) == LOW && isPulseHigh) {
      isPulseHigh = false;
    }
  }

  if (elapsedSeconds == 6) { // Measure over 6 seconds for better accuracy
    heartBeatsPerMinute = heartBeatCount*10 ;
    isCounting = false;

    lcd.setCursor(0, 2);
    lcd.print(" HB Per Min: ");
    lcd.print(heartBeatsPerMinute);
    lcd.print("  ");
    lcd.setCursor(0, 3);
    lcd.print(" Press Button Again.");

    heartBeatCount = 0;
    elapsedSeconds = 0;

    Serial.print("HB Per Min: ");
    Serial.println(heartBeatsPerMinute);
  }
}

void timerIsr() {
  if (isCounting) {
    elapsedSeconds++;
    lcd.setCursor(14, 3);
    lcd.print(elapsedSeconds);
    lcd.print("       ");
  }
}
