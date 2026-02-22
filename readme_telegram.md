# How to use it

## How it's work:
ברגע שהקונטיינר של ה-Docker רץ, הוא הופך ל"מנוע" שמחבר בין **OpenClaw** לבין השרתים של **Telegram**. התקשורת עצמה מתבצעת בשני כיוונים, והנה איך זה נראה בפועל:

### 1. השלב הראשון: יצירת הבוט בטלגרם (אם עוד לא עשית זאת)

כדי שהקוד בתוך ה-Docker ידע לאן לשלוח הודעות, אתה צריך "כתובת" (Token):

1. חפש בטלגרם את המשתמש **`@BotFather`**.
2. שלח לו את הפקודה `/newbot`.
3. בחר שם לבוט (למשל: `@YourName_bot`) ושם משתמש (חייב להסתיים ב-`_bot`).
4. הוא ישלח לך הודעה עם ה-**HTTP API Token** (מחרוזת ארוכה של תווים). זה המפתח שלך.

---

### 2. הזנת המפתח ל-Docker

בתוך קובץ ה-`docker-compose.yml` שכתבנו קודם, יש שורה של `environment`. אתה צריך להדביק שם את הטוקן שקיבלת:

```yaml
environment:
  - TELEGRAM_TOKEN=1234567890:ABCdefGHiJkLmNoPqRsTuVwXyZ # הטוקן מה-BotFather
  - OLLAMA_BASE_URL=http://host.docker.internal:11434

```

#### מציאת ה ID
כך תמצא את ה-ID שלך:
חפש בטלגרם את הבוט: @userinfobot (יש לו בדרך כלל תמונה של איש עם סימן שאלה).

לחץ על Start.

הבוט ישלח לך מיד הודעה עם ה-Id שלך (מספר ארוך של 9-10 ספרות).


```yaml
environment:
  - MY_USER_ID=1234567890 # id from @userinfobot

```

לאחר שעדכנת, הרץ שוב:
`docker-compose up -d`

---

### 3. איך אתה מדבר איתו עכשיו?

ברגע שהקונטיינר רץ והלוגים שלו מראים שהוא התחבר בהצלחה (אתה יכול לבדוק עם `docker logs openclaw_telegram_bot`), בצע את הפעולות הבאות:

1. פתח את אפליקציית טלגרם בטלפון או במחשב.
2. חפש את הבוט שיצרת לפי שם המשתמש שלו (למשל `@YourName_bot`).
3. לחץ על **Start**.
4. **שלח הודעה:** למשל, *"תבדוק מה הטמפרטורה עכשיו בתל אביב"*.

---

### 4. מה קורה "מתחת למכסה המנוע"? (מסלול ההודעה)

כדי שתבין מה קורה ואיפה זה עלול להיתקע:

1. **אתה (טלגרם):** שולח הודעה לשרתים של טלגרם.
2. **ה-Docker (קוד הבוט):** הקונטיינר שלך פונה לשרתים של טלגרם (בשיטה שנקראת Polling) ושואל: "יש הודעות חדשות עבורי?".
3. **העיבוד:** הקוד מקבל את ההודעה, שולח אותה ל-**Ollama** (שנמצא מחוץ ל-Docker) כדי להבין מה לעשות.
4. **הפעולה:** **OpenClaw** פותח דפדפן (בתוך ה-Docker), מבצע את המשימה, ומצלם מסך.
5. **התגובה:** הבוט שולח את התשובה ואת התמונה חזרה לשרתים של טלגרם, ואתה רואה אותם בטלפון.

---

### טיפ לפתרון בעיות (Debugging)

אם שלחת הודעה והבוט לא עונה:

1. **בדוק שהקונטיינר חי:** `docker ps`
2. **צפה בלוגים בזמן אמת:**
```bash
docker logs -f openclaw_telegram_bot

```


כאן תראה אם יש שגיאת חיבור ל-Ollama או שהטוקן של טלגרם לא תקין.

**האם הצלחת להוציא את הטוקן מה-BotFather, או שנתקלת בבעיה בשלב הזה?**

## How to Pairing
// sending
Yan, [19-Feb-26 13:24]
/start

// reciving
@Yaniv_bot, [19-Feb-26 13:24]
OpenClaw: access not configured.

Your Telegram user id: 6977408305

Pairing code: ZADX65W4

Ask the bot owner to approve with:
openclaw pairing approve telegram ZADX65W4

---

## Bot Commands

The bot supports the following commands:

- `/help` - Show the help menu with all available commands and features.
- `/new` - Start a new session (clear conversation history).
- `/stop` - Stop the current conversation (this does NOT affect schedules).
- `/restart` - Restart the session (completes a stop followed by a new session).
- `/schedule <name> <seconds> <prompt>` - Schedule a recurring task.
  - Example: `/schedule btc 600 Check the price of Bitcoin`
- `/stopschedule [name]` - Stop a specific schedule by name, or all if no name is provided.
- `/schedules` - List all currently running schedules.

You can also:
- Send any text message to chat with the bot.
- Send a photo to save it (use the caption as the filename).
- Type `get pic <filename>` to retrieve a saved photo.
