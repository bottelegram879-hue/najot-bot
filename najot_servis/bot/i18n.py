"""All user-facing texts in three languages. t(lang, key, **kw) -> str (HTML)."""

LANGS = {"uz": "🇺🇿 O‘zbekcha", "ru": "🇷🇺 Русский", "en": "🇬🇧 English"}
DEFAULT_LANG = "ru"

T: dict[str, dict[str, str]] = {
    # ---------- common ----------
    "choose_lang": {
        "ru": "🌐 Выберите язык:", "uz": "🌐 Tilni tanlang:", "en": "🌐 Choose your language:"},
    "lang_set": {"ru": "✅ Язык: Русский", "uz": "✅ Til: O‘zbekcha", "en": "✅ Language: English"},
    "welcome": {
        "ru": "🚛 <b>NAJOT SERVIS</b> · сервис грузовых автомобилей\nДобро пожаловать!\n\n🔧 Ремонт, диагностика и ТО грузовиков\n🆘 Выездной ремонт и эвакуация\n📲 Статус ремонта — прямо в Telegram\n\n<b>Что хотите сделать?</b>",
        "uz": "🚛 <b>NAJOT SERVIS</b> · yuk mashinalari servisi\nXush kelibsiz!\n\n🔧 Yuk mashinalarini ta’mirlash, diagnostika va TXK\n🆘 Joyiga chiqib ta’mirlash va evakuatsiya\n📲 Ta’mirlash holati — Telegramda\n\n<b>Nima qilmoqchisiz?</b>",
        "en": "🚛 <b>NAJOT SERVIS</b> · truck service centre\nWelcome!\n\n🔧 Truck repair, diagnostics and maintenance\n🆘 Mobile repair and towing\n📲 Repair status right in Telegram\n\n<b>What would you like to do?</b>"},
    "btn_book": {"ru": "🔧 Записать грузовик на ремонт", "uz": "🔧 Yuk mashinasini ta’mirga yozish", "en": "🔧 Book a truck repair"},
    "btn_sos": {"ru": "🆘 Сломался в пути", "uz": "🆘 Yo‘lda buzildi", "en": "🆘 Broke down on the road"},
    "btn_my_request": {"ru": "📋 Моя заявка", "uz": "📋 Mening arizam", "en": "📋 My request"},
    "btn_my_requests": {"ru": "📦 Мои заявки", "uz": "📦 Arizalarim", "en": "📦 My requests"},
    "btn_my_cars": {"ru": "🚛 Мой грузовик", "uz": "🚛 Mening yuk mashinam", "en": "🚛 My trucks"},
    "btn_contact_master": {"ru": "💬 Связаться с мастером", "uz": "💬 Usta bilan bog‘lanish", "en": "💬 Contact the mechanic"},
    "btn_address": {"ru": "📍 Адрес автосервиса", "uz": "📍 Avtoservis manzili", "en": "📍 Service address"},
    "btn_call": {"ru": "📞 Позвонить", "uz": "📞 Qo‘ng‘iroq qilish", "en": "📞 Call us"},
    "btn_about": {"ru": "ℹ️ О сервисе", "uz": "ℹ️ Servis haqida", "en": "ℹ️ About us"},
    "btn_ai": {"ru": "🤖 AI-помощник", "uz": "🤖 AI-yordamchi", "en": "🤖 AI assistant"},
    "btn_lang": {"ru": "🌐 Язык", "uz": "🌐 Til", "en": "🌐 Language"},
    "btn_back": {"ru": "⬅️ Назад", "uz": "⬅️ Orqaga", "en": "⬅️ Back"},
    "btn_home": {"ru": "🏠 Главное меню", "uz": "🏠 Bosh menyu", "en": "🏠 Main menu"},
    "btn_cancel": {"ru": "✖️ Отмена", "uz": "✖️ Bekor qilish", "en": "✖️ Cancel"},
    "btn_skip": {"ru": "⏭ Пропустить", "uz": "⏭ O‘tkazib yuborish", "en": "⏭ Skip"},
    "btn_yes": {"ru": "✅ Да", "uz": "✅ Ha", "en": "✅ Yes"},
    "btn_no": {"ru": "✖️ Нет", "uz": "✖️ Yo‘q", "en": "✖️ No"},
    "btn_prev": {"ru": "◀️", "uz": "◀️", "en": "◀️"},
    "btn_next": {"ru": "▶️", "uz": "▶️", "en": "▶️"},
    "btn_client_mode": {"ru": "👤 Режим клиента", "uz": "👤 Mijoz rejimi", "en": "👤 Client mode"},
    "btn_staff_panel": {"ru": "🧰 Моя панель", "uz": "🧰 Mening panelim", "en": "🧰 My panel"},
    "cancelled": {"ru": "✖️ Действие отменено.", "uz": "✖️ Amal bekor qilindi.", "en": "✖️ Cancelled."},
    "access_denied": {"ru": "⛔ Нет доступа.", "uz": "⛔ Ruxsat yo‘q.", "en": "⛔ Access denied."},
    "error_generic": {
        "ru": "⚠️ Произошла ошибка. Попробуйте ещё раз или нажмите /start.",
        "uz": "⚠️ Xatolik yuz berdi. Qayta urinib ko‘ring yoki /start bosing.",
        "en": "⚠️ Something went wrong. Please try again or press /start."},
    "too_fast": {"ru": "⏳ Слишком быстро, подождите секунду.", "uz": "⏳ Juda tez, bir soniya kuting.", "en": "⏳ Too fast, wait a second."},
    "not_found": {"ru": "🔎 Не найдено.", "uz": "🔎 Topilmadi.", "en": "🔎 Not found."},
    "use_buttons": {
        "ru": "👇 Пожалуйста, используйте кнопки ниже.",
        "uz": "👇 Iltimos, quyidagi tugmalardan foydalaning.",
        "en": "👇 Please use the buttons below."},
    "about_text": {
        "ru": "🚛 <b>Najot.Servis Грузовых</b> 🚛\nКачественный ремонт грузовых автомобилей!\n\n✅ Ремонт двигателей любой сложности.\n✅ Ремонт коробок передач.\n✅ Современная компьютерная диагностика.\n✅ Ремонт автоэлектрики с использованием современного оборудования.\n✅ Быстрое и качественное обслуживание.\n\n📞 <b>Телефоны:</b>\n{phone}\n{phone2}\n\n📍 <b>Адрес:</b>\n{address}\n\n🕐 {hours}",
        "uz": "🚛 <b>Najot.Servis Yuk mashinalari</b> 🚛\nYuk mashinalarini sifatli ta’mirlash!\n\n✅ Har qanday murakkablikdagi dvigatellarni ta’mirlash.\n✅ Uzatmalar qutisini ta’mirlash.\n✅ Zamonaviy kompyuter diagnostikasi.\n✅ Zamonaviy uskunalar yordamida avtoelektrikani ta’mirlash.\n✅ Tez va sifatli xizmat.\n\n📞 <b>Telefonlar:</b>\n{phone}\n{phone2}\n\n📍 <b>Manzil:</b>\n{address}\n\n🕐 {hours}",
        "en": "🚛 <b>Najot.Servis Trucks</b> 🚛\nQuality truck repair!\n\n✅ Engine repair of any complexity.\n✅ Gearbox repair.\n✅ Modern computer diagnostics.\n✅ Auto-electrics repair with modern equipment.\n✅ Fast, high-quality service.\n\n📞 <b>Phones:</b>\n{phone}\n{phone2}\n\n📍 <b>Address:</b>\n{address}\n\n🕐 {hours}"},
    "contacts_text": {
        "ru": "📍 <b>Адрес:</b>\n{address}\n\n📞 <b>Телефоны:</b> {phone}, {phone2}\n💬 <b>Telegram:</b> @{telegram}\n📸 <b>Instagram:</b> @{instagram}\n🕐 <b>Режим работы:</b> {hours}",
        "uz": "📍 <b>Manzil:</b>\n{address}\n\n📞 <b>Telefonlar:</b> {phone}, {phone2}\n💬 <b>Telegram:</b> @{telegram}\n📸 <b>Instagram:</b> @{instagram}\n🕐 <b>Ish vaqti:</b> {hours}",
        "en": "📍 <b>Address:</b>\n{address}\n\n📞 <b>Phones:</b> {phone}, {phone2}\n💬 <b>Telegram:</b> @{telegram}\n📸 <b>Instagram:</b> @{instagram}\n🕐 <b>Working hours:</b> {hours}"},
    "call_text": {
        "ru": "📞 Нажмите на контакт ниже, чтобы позвонить в NAJOT SERVIS:\n<b>{phone}</b>",
        "uz": "📞 NAJOT SERVISga qo‘ng‘iroq qilish uchun quyidagi kontaktni bosing:\n<b>{phone}</b>",
        "en": "📞 Tap the contact below to call NAJOT SERVIS:\n<b>{phone}</b>"},
    "btn_tg": {"ru": "💬 Telegram", "uz": "💬 Telegram", "en": "💬 Telegram"},
    "btn_ig": {"ru": "📸 Instagram", "uz": "📸 Instagram", "en": "📸 Instagram"},
    "btn_map": {"ru": "📍 Открыть карту", "uz": "📍 Xaritani ochish", "en": "📍 Open map"},

    # ---------- booking wizard ----------
    "bk_header": {
        "ru": "📝 <b>Заявка на ремонт грузовика</b> · шаг {i}/{n}\n\n",
        "uz": "📝 <b>Yuk mashinasini ta’mirlash arizasi</b> · {i}/{n}-qadam\n\n",
        "en": "📝 <b>Truck repair request</b> · step {i}/{n}\n\n"},
    "bk_step_brand": {
        "ru": "🚛 Выберите <b>марку грузовика</b>\n🔎 или просто <b>напишите название</b> для поиска:",
        "uz": "🚛 <b>Yuk mashinasi markasini</b> tanlang\n🔎 yoki qidirish uchun <b>nomini yozing</b>:",
        "en": "🚛 Choose the <b>truck brand</b>\n🔎 or just <b>type its name</b> to search:"},
    "bk_saved_cars": {
        "ru": "\n\n⭐ Или выберите сохранённый грузовик:",
        "uz": "\n\n⭐ Yoki saqlangan yuk mashinasini tanlang:",
        "en": "\n\n⭐ Or pick one of your saved trucks:"},
    "btn_other_brand": {"ru": "✍️ Другая марка", "uz": "✍️ Boshqa marka", "en": "✍️ Other brand"},
    "bk_type_brand": {
        "ru": "✍️ Напишите марку грузовика:", "uz": "✍️ Yuk mashinasi markasini yozing:", "en": "✍️ Type the truck brand:"},
    "bk_search_results": {
        "ru": "🔎 Результаты поиска «{q}»:", "uz": "🔎 «{q}» bo‘yicha natijalar:", "en": "🔎 Results for “{q}”:"},
    "btn_use_typed": {"ru": "✅ Использовать «{q}»", "uz": "✅ «{q}» ni tanlash", "en": "✅ Use “{q}”"},
    "bk_step_model": {
        "ru": "🚛 Марка: <b>{brand}</b>\n\nВыберите <b>модель</b> кнопкой 👇\nили напишите её сообщением, или нажмите «⏭ Пропустить».",
        "uz": "🚛 Marka: <b>{brand}</b>\n\n<b>Modelni</b> tugma orqali tanlang 👇\nyoki xabar qilib yozing, yoki «⏭ O‘tkazib yuborish» ni bosing.",
        "en": "🚛 Brand: <b>{brand}</b>\n\nPick the <b>model</b> below 👇\nor type it, or tap “⏭ Skip”."},
    "bk_step_year": {
        "ru": "📅 Выберите или введите <b>год выпуска</b>:",
        "uz": "📅 <b>Ishlab chiqarilgan yilini</b> tanlang yoki kiriting:",
        "en": "📅 Choose or type the <b>year</b> of manufacture:"},
    "bk_bad_year": {
        "ru": "⚠️ Введите год цифрами от 1960 до {max}.",
        "uz": "⚠️ Yilni 1960 dan {max} gacha raqamda kiriting.",
        "en": "⚠️ Enter a year between 1960 and {max}."},
    "bk_step_body": {
        "ru": "🚛 Выберите <b>тип грузовика</b>:", "uz": "🚛 <b>Yuk mashinasi turini</b> tanlang:", "en": "🚛 Choose the <b>truck type</b>:"},
    "bk_step_plate": {
        "ru": "🔢 Введите <b>госномер</b> (например 30 A 123 BC) или пропустите:",
        "uz": "🔢 <b>Davlat raqamini</b> kiriting (masalan 30 A 123 BC) yoki o‘tkazib yuboring:",
        "en": "🔢 Enter the <b>plate number</b> (e.g. 30 A 123 BC) or skip:"},
    "bk_step_problem": {
        "ru": "⚠️ <b>Опишите проблему</b>\n\n<i>Например: «Не набирает мощность, чёрный дым», «Травит воздух в тормозах», «Горит Check Engine»</i>\n\n📷 Можно отправить <b>фото</b> с подписью.",
        "uz": "⚠️ <b>Muammoni yozing</b>\n\n<i>Masalan: «Quvvat olmayapti, qora tutun», «Tormozdan havo chiqyapti», «Check Engine yonyapti»</i>\n\n📷 Izoh bilan <b>rasm</b> yuborish mumkin.",
        "en": "⚠️ <b>Describe the problem</b>\n\n<i>e.g. “Loss of power, black smoke”, “Air leaking from brakes”, “Check Engine is on”</i>\n\n📷 You can send a <b>photo</b> with a caption."},
    "bk_photo_ok": {"ru": "📷 Фото прикреплено.", "uz": "📷 Rasm biriktirildi.", "en": "📷 Photo attached."},
    "bk_problem_short": {
        "ru": "⚠️ Опишите проблему чуть подробнее (минимум 5 символов).",
        "uz": "⚠️ Muammoni biroz batafsilroq yozing (kamida 5 belgi).",
        "en": "⚠️ Please describe the problem in a bit more detail (min 5 chars)."},
    "bk_too_long": {
        "ru": "⚠️ Слишком длинный текст (максимум {n} символов).",
        "uz": "⚠️ Matn juda uzun (ko‘pi bilan {n} belgi).",
        "en": "⚠️ Text is too long (max {n} characters)."},
    "bk_step_service": {"ru": "🔧 Выберите <b>услугу</b>:", "uz": "🔧 <b>Xizmatni</b> tanlang:", "en": "🔧 Choose a <b>service</b>:"},
    "bk_step_mobility": {
        "ru": "🚛 <b>Как поступим?</b>\n\n🚛 <b>Приеду сам</b> — пришлём точку сервиса на карте, чтобы вы легко доехали.\n🆘 <b>Вызов</b> — мастер приедет к вам, нужна ваша геолокация.",
        "uz": "🚛 <b>Qanday qilamiz?</b>\n\n🚛 <b>O‘zim kelaman</b> — oson yetib kelishingiz uchun servis joylashuvini xaritada yuboramiz.\n🆘 <b>Chaqiruv</b> — usta sizning oldingizga keladi, geolokatsiyangiz kerak.",
        "en": "🚛 <b>How shall we proceed?</b>\n\n🚛 <b>I’ll come myself</b> — we’ll send you the service location on the map.\n🆘 <b>Call-out</b> — a mechanic comes to you; we need your location."},
    "bk_step_location": {
        "ru": "📍 <b>Отправьте геолокацию</b>, где сейчас грузовик.\n\n👇 Нажмите кнопку «📍 Отправить геолокацию» внизу экрана — мастер сразу получит точку на карте.",
        "uz": "📍 Yuk mashinasi hozir turgan joyning <b>geolokatsiyasini yuboring</b>.\n\n👇 Ekran pastidagi «📍 Geolokatsiyani yuborish» tugmasini bosing — usta darhol xaritadagi nuqtani oladi.",
        "en": "📍 <b>Send the location</b> where the truck is now.\n\n👇 Tap “📍 Send location” at the bottom of the screen — the mechanic will get the pin right away."},
    "bk_need_location": {
        "ru": "⚠️ Для вызова нужна геолокация. Нажмите кнопку «📍 Отправить геолокацию» внизу (на телефоне должна быть включена геолокация).",
        "uz": "⚠️ Chaqiruv uchun geolokatsiya kerak. Pastdagi «📍 Geolokatsiyani yuborish» tugmasini bosing (telefonda geolokatsiya yoqilgan bo‘lishi kerak).",
        "en": "⚠️ A call-out needs your location. Tap “📍 Send location” at the bottom (location services must be on)."},
    "bk_come_here": {
        "ru": "📍 <b>Ждём вас в NAJOT SERVIS!</b>\n{address}\n🕐 {hours}\n\nНажмите на точку ниже, чтобы построить маршрут 👇",
        "uz": "📍 <b>Sizni NAJOT SERVISda kutamiz!</b>\n{address}\n🕐 {hours}\n\nYo‘nalish qurish uchun quyidagi nuqtani bosing 👇",
        "en": "📍 <b>We’re waiting for you at NAJOT SERVIS!</b>\n{address}\n🕐 {hours}\n\nTap the pin below to get directions 👇"},
    "btn_route": {"ru": "🧭 Маршрут", "uz": "🧭 Yo‘nalish", "en": "🧭 Directions"},
    "set_location": {"ru": "🗺 Точка на карте", "uz": "🗺 Xaritadagi nuqta", "en": "🗺 Map pin"},
    "set_location_hint": {
        "ru": "🗺 Отправьте геолокацию (📎 → Геопозиция) или ссылку Google Maps / координаты «39.6127,66.99435»:",
        "uz": "🗺 Geolokatsiyani (📎 → Joylashuv) yoki Google Maps havolasini / «39.6127,66.99435» koordinatalarini yuboring:",
        "en": "🗺 Send a location (📎 → Location) or a Google Maps link / coordinates “39.6127,66.99435”:"},
    "set_location_bad": {
        "ru": "⚠️ Не удалось распознать координаты.", "uz": "⚠️ Koordinatalarni aniqlab bo‘lmadi.", "en": "⚠️ Could not read the coordinates."},
    "btn_send_location": {"ru": "📍 Отправить геолокацию", "uz": "📍 Geolokatsiyani yuborish", "en": "📍 Send location"},
    "bk_location_ok": {"ru": "✅ Местоположение получено", "uz": "✅ Joylashuv qabul qilindi", "en": "✅ Location received"},
    "bk_step_name": {"ru": "👤 Введите ваше <b>имя</b>:", "uz": "👤 <b>Ismingizni</b> kiriting:", "en": "👤 Enter your <b>name</b>:"},
    "btn_use_name": {"ru": "👤 {name}", "uz": "👤 {name}", "en": "👤 {name}"},
    "bk_step_phone": {
        "ru": "📞 Отправьте <b>номер телефона</b> кнопкой ниже или введите вручную (+998...):",
        "uz": "📞 <b>Telefon raqamingizni</b> quyidagi tugma orqali yuboring yoki qo‘lda kiriting (+998...):",
        "en": "📞 Send your <b>phone number</b> with the button below or type it (+998...):"},
    "body_tractor": {"ru": "Тягач", "uz": "Tyagach", "en": "Tractor unit"},
    "body_dump": {"ru": "Самосвал", "uz": "Samosval", "en": "Dump truck"},
    "body_flatbed": {"ru": "Бортовой", "uz": "Bortli", "en": "Flatbed"},
    "body_van": {"ru": "Фургон", "uz": "Furgon", "en": "Box van"},
    "body_reefer": {"ru": "Рефрижератор", "uz": "Refrijerator", "en": "Reefer"},
    "body_tanker": {"ru": "Цистерна", "uz": "Sisterna", "en": "Tanker"},
    "body_special": {"ru": "Спецтехника", "uz": "Maxsus texnika", "en": "Special vehicle"},
    "body_light": {"ru": "Малотоннажный (до 3.5 т)", "uz": "Kichik yuk mashinasi (3.5 t gacha)", "en": "Light truck (≤3.5 t)"},
    "body_other": {"ru": "Другой", "uz": "Boshqa", "en": "Other"},
    "mob_drive": {"ru": "Приеду сам", "uz": "O‘zim kelaman", "en": "I’ll come myself"},
    "mob_onsite": {"ru": "Вызов мастера", "uz": "Usta chaqiruvi", "en": "Call a mechanic"},
    "mob_tow": {"ru": "Нужен эвакуатор", "uz": "Evakuator kerak", "en": "Need a tow truck"},
    "lbl_body": {"ru": "🚚 Тип", "uz": "🚚 Turi", "en": "🚚 Type"},
    "lbl_mobility": {"ru": "📍 Доставка", "uz": "📍 Yetkazish", "en": "📍 Delivery"},
    "lbl_location": {"ru": "🗺 Где грузовик", "uz": "🗺 Mashina joyi", "en": "🗺 Truck location"},
    "lbl_photo": {"ru": "📷 Фото приложено", "uz": "📷 Rasm biriktirilgan", "en": "📷 Photo attached"},
    "map_link": {"ru": "открыть карту", "uz": "xaritada ochish", "en": "open map"},
    "urgent": {"ru": "🆘 СРОЧНО · ", "uz": "🆘 SHOSHILINCH · ", "en": "🆘 URGENT · "},
    "sos_intro": {
        "ru": "🆘 <b>Грузовик сломался в пути?</b>\n\nОформим срочную заявку за минуту: марка, что случилось и где вы находитесь. Мастер свяжется с вами как можно скорее.\n\n📞 Если ситуация опасная — сразу звоните: <b>{phone}</b>",
        "uz": "🆘 <b>Yuk mashinasi yo‘lda buzildimi?</b>\n\nBir daqiqada shoshilinch ariza tuzamiz: marka, nima bo‘ldi va qayerdasiz. Usta imkon qadar tez bog‘lanadi.\n\n📞 Vaziyat xavfli bo‘lsa — darhol qo‘ng‘iroq qiling: <b>{phone}</b>",
        "en": "🆘 <b>Truck broke down on the road?</b>\n\nWe’ll file an urgent request in a minute: brand, what happened and where you are. A mechanic will contact you as soon as possible.\n\n📞 If the situation is dangerous, call right away: <b>{phone}</b>"},
    "btn_sos_start": {"ru": "🆘 Оформить срочную заявку", "uz": "🆘 Shoshilinch ariza", "en": "🆘 File urgent request"},
    "btn_send_phone": {"ru": "📱 Отправить мой номер", "uz": "📱 Raqamimni yuborish", "en": "📱 Send my number"},
    "bk_bad_phone": {
        "ru": "⚠️ Неверный номер. Пример: +998901234567",
        "uz": "⚠️ Noto‘g‘ri raqam. Namuna: +998901234567",
        "en": "⚠️ Invalid number. Example: +998901234567"},
    "bk_phone_ok": {"ru": "✅ Номер получен", "uz": "✅ Raqam qabul qilindi", "en": "✅ Number received"},
    "bk_preview": {
        "ru": "🔎 <b>Проверьте заявку</b>\n\n{card}\n\nВсё верно?",
        "uz": "🔎 <b>Arizani tekshiring</b>\n\n{card}\n\nHammasi to‘g‘rimi?",
        "en": "🔎 <b>Check your request</b>\n\n{card}\n\nIs everything correct?"},
    "btn_confirm": {"ru": "✅ Подтвердить заявку", "uz": "✅ Arizani tasdiqlash", "en": "✅ Confirm request"},
    "btn_edit": {"ru": "✏️ Изменить", "uz": "✏️ O‘zgartirish", "en": "✏️ Edit"},
    "bk_edit_what": {"ru": "✏️ Что изменить?", "uz": "✏️ Nimani o‘zgartiramiz?", "en": "✏️ What would you like to change?"},
    "f_brand": {"ru": "🚛 Марка", "uz": "🚛 Marka", "en": "🚛 Brand"},
    "f_model": {"ru": "🚚 Модель", "uz": "🚚 Model", "en": "🚚 Model"},
    "f_year": {"ru": "📅 Год", "uz": "📅 Yil", "en": "📅 Year"},
    "f_problem": {"ru": "⚠️ Проблема", "uz": "⚠️ Muammo", "en": "⚠️ Problem"},
    "f_service": {"ru": "🔧 Услуга", "uz": "🔧 Xizmat", "en": "🔧 Service"},
    "f_name": {"ru": "👤 Имя", "uz": "👤 Ism", "en": "👤 Name"},
    "f_phone": {"ru": "📞 Телефон", "uz": "📞 Telefon", "en": "📞 Phone"},
    "f_plate": {"ru": "🔢 Госномер", "uz": "🔢 Davlat raqami", "en": "🔢 Plate"},
    "f_body": {"ru": "🚚 Тип", "uz": "🚚 Turi", "en": "🚚 Type"},
    "f_mobility": {"ru": "📍 Доставка", "uz": "📍 Yetkazish", "en": "📍 Delivery"},
    "bk_processing": {"ru": "⏳ Заявка уже обрабатывается…", "uz": "⏳ Ariza allaqachon ishlanmoqda…", "en": "⏳ Request is already being processed…"},
    "bk_expired": {
        "ru": "⚠️ Сессия оформления устарела. Начните заново.",
        "uz": "⚠️ Ariza sessiyasi eskirgan. Qaytadan boshlang.",
        "en": "⚠️ This booking session has expired. Please start again."},
    "bk_created": {
        "ru": "✅ <b>Заявка успешно создана!</b>\n\n🎫 Заявка №<b>{number}</b>\n\nВаша заявка передана специалисту NAJOT SERVIS.\nМы скоро свяжемся с вами.\n\nСтатус: 🟡 <b>Новая заявка</b>",
        "uz": "✅ <b>Ariza muvaffaqiyatli yaratildi!</b>\n\n🎫 Ariza №<b>{number}</b>\n\nArizangiz NAJOT SERVIS mutaxassisiga yuborildi.\nTez orada siz bilan bog‘lanamiz.\n\nHolat: 🟡 <b>Yangi ariza</b>",
        "en": "✅ <b>Request created successfully!</b>\n\n🎫 Request №<b>{number}</b>\n\nYour request has been sent to a NAJOT SERVIS specialist.\nWe will contact you soon.\n\nStatus: 🟡 <b>New request</b>"},
    "btn_open_request": {"ru": "📋 Открыть заявку", "uz": "📋 Arizani ochish", "en": "📋 Open request"},
    "bk_save_car_q": {
        "ru": "💾 Сохранить этот грузовик в «Мой грузовик»?",
        "uz": "💾 Bu yuk mashinasini «Mening yuk mashinam»ga saqlaymizmi?",
        "en": "💾 Save this truck to “My trucks”?"},
    "bk_created_owner": {
        "ru": "✅ Заявка №<b>{number}</b> создана.", "uz": "✅ Ariza №<b>{number}</b> yaratildi.", "en": "✅ Request №<b>{number}</b> created."},

    # ---------- request form (same fields as the website form) ----------
    "form_title": {
        "ru": "📝 <b>Заявка на ремонт грузовика</b>\n<i>* — обязательные поля</i>",
        "uz": "📝 <b>Yuk mashinasini ta’mirlash arizasi</b>\n<i>* — majburiy maydonlar</i>",
        "en": "📝 <b>Truck repair request</b>\n<i>* — required fields</i>"},
    "form_title_sos": {
        "ru": "🆘 <b>Срочная заявка — вызов мастера</b>\n<i>* — обязательные поля</i>",
        "uz": "🆘 <b>Shoshilinch ariza — usta chaqiruvi</b>\n<i>* — majburiy maydonlar</i>",
        "en": "🆘 <b>Urgent request — call a mechanic</b>\n<i>* — required fields</i>"},
    "form_remembered": {
        "ru": "♻️ <i>Заполнено по прошлой заявке — проверьте и при необходимости измените.</i>",
        "uz": "♻️ <i>Oldingi ariza bo‘yicha to‘ldirildi — tekshiring va kerak bo‘lsa o‘zgartiring.</i>",
        "en": "♻️ <i>Filled in from your last request — check and change if needed.</i>"},
    "btn_other_truck": {"ru": "🆕 Другой грузовик", "uz": "🆕 Boshqa yuk mashinasi", "en": "🆕 Another truck"},
    "open_form_text": {
        "ru": "📝 <b>Заявка на ремонт</b>\nНажмите кнопку ниже — откроется форма заявки.",
        "uz": "📝 <b>Ta’mirlash arizasi</b>\nQuyidagi tugmani bosing — ariza shakli ochiladi.",
        "en": "📝 <b>Repair request</b>\nTap the button below — the request form will open."},
    "btn_open_form": {"ru": "📝 Открыть форму заявки", "uz": "📝 Ariza shaklini ochish", "en": "📝 Open request form"},
    "btn_fill_in_chat": {"ru": "💬 Заполнить в чате", "uz": "💬 Chatda to‘ldirish", "en": "💬 Fill in chat"},
    "form_agree": {
        "ru": "<i>Нажимая «Отправить заявку», вы соглашаетесь, что мастер свяжется с вами по указанному номеру.</i>",
        "uz": "<i>«Arizani yuborish» tugmasini bosib, usta ko‘rsatilgan raqam orqali siz bilan bog‘lanishiga rozilik bildirasiz.</i>",
        "en": "<i>By tapping “Send request” you agree that a mechanic will contact you at the number provided.</i>"},
    "ff_name": {"ru": "👤 Имя", "uz": "👤 Ism", "en": "👤 Name"},
    "ff_phone": {"ru": "📞 Телефон", "uz": "📞 Telefon", "en": "📞 Phone"},
    "ff_brand": {"ru": "🚛 Марка", "uz": "🚛 Marka", "en": "🚛 Brand"},
    "ff_model": {"ru": "🚚 Модель", "uz": "🚚 Model", "en": "🚚 Model"},
    "ff_car_desc": {"ru": "📋 Описание автомобиля", "uz": "📋 Mashina tavsifi", "en": "📋 Truck details"},
    "ff_services": {"ru": "🔧 Услуги", "uz": "🔧 Xizmatlar", "en": "🔧 Services"},
    "q_services": {
        "ru": "🔧 <b>Выберите услуги</b> — можно несколько, нажмите ещё раз, чтобы убрать:",
        "uz": "🔧 <b>Xizmatlarni tanlang</b> — bir nechtasini tanlash mumkin, olib tashlash uchun yana bosing:",
        "en": "🔧 <b>Choose services</b> — several are allowed, tap again to remove:"},
    "ff_problem": {"ru": "⚠️ Описание проблемы", "uz": "⚠️ Muammo tavsifi", "en": "⚠️ Problem"},
    "ff_date": {"ru": "📅 Желаемая дата", "uz": "📅 Qulay sana", "en": "📅 Preferred date"},
    "ff_mobility": {"ru": "📍 Где ремонтировать", "uz": "📍 Qayerda ta’mirlash", "en": "📍 Where to repair"},
    "ff_location": {"ru": "🗺 Где находится машина", "uz": "🗺 Mashina qayerda", "en": "🗺 Where the truck is"},
    "ff_photos": {"ru": "📷 Фото", "uz": "📷 Rasm", "en": "📷 Photos"},
    "ff_photos_val": {"ru": "{n} из 3", "uz": "{n} / 3", "en": "{n} of 3"},
    "ff_location_set": {"ru": "📍 точка на карте", "uz": "📍 xaritadagi nuqta", "en": "📍 map pin"},
    "btn_next_field": {"ru": "➡️ Далее: {field}", "uz": "➡️ Keyingi: {field}", "en": "➡️ Next: {field}"},
    "btn_add_photo": {"ru": "📷 Добавить фото ({n}/3)", "uz": "📷 Rasm qo‘shish ({n}/3)", "en": "📷 Add photo ({n}/3)"},
    "btn_mark_location": {"ru": "📍 Отметить мою локацию", "uz": "📍 Joylashuvimni belgilash", "en": "📍 Mark my location"},
    "btn_send_request": {"ru": "📤 ОТПРАВИТЬ ЗАЯВКУ", "uz": "📤 ARIZANI YUBORISH", "en": "📤 SEND REQUEST"},
    "btn_ask_ai": {"ru": "🤖 Спросить NAJOT AI", "uz": "🤖 NAJOT AI dan so‘rash", "en": "🤖 Ask NAJOT AI"},
    "btn_to_form": {"ru": "⬅️ К заявке", "uz": "⬅️ Arizaga", "en": "⬅️ Back to form"},
    "btn_done": {"ru": "✅ Готово", "uz": "✅ Tayyor", "en": "✅ Done"},
    "btn_clear_photos": {"ru": "🗑 Удалить фото", "uz": "🗑 Rasmlarni o‘chirish", "en": "🗑 Remove photos"},
    "btn_no_date": {"ru": "Без даты", "uz": "Sanasiz", "en": "No date"},
    "form_missing": {
        "ru": "⚠️ Заполните обязательные поля: {fields}", "uz": "⚠️ Majburiy maydonlarni to‘ldiring: {fields}",
        "en": "⚠️ Please fill in: {fields}"},
    "q_name": {"ru": "👤 <b>Как к вам обращаться?</b>\nНапишите имя:", "uz": "👤 <b>Sizga qanday murojaat qilaylik?</b>\nIsmingizni yozing:", "en": "👤 <b>How should we address you?</b>\nType your name:"},
    "q_car_desc": {
        "ru": "📋 <b>Описание автомобиля</b>\nГод, двигатель, пробег, госномер — что знаете:",
        "uz": "📋 <b>Mashina tavsifi</b>\nYil, dvigatel, probeg, davlat raqami — nimani bilsangiz:",
        "en": "📋 <b>Truck details</b>\nYear, engine, mileage, plate — whatever you know:"},
    "q_problem": {
        "ru": "⚠️ <b>Описание проблемы</b>\nЧто случилось? Какие ошибки на панели, когда проявляется неисправность…\n\n📷 Можно отправить фото с подписью.",
        "uz": "⚠️ <b>Muammo tavsifi</b>\nNima bo‘ldi? Paneldagi xatolar, nosozlik qachon namoyon bo‘ladi…\n\n📷 Izohli rasm yuborish mumkin.",
        "en": "⚠️ <b>Problem</b>\nWhat happened? Any dashboard errors, when does the fault appear…\n\n📷 You can send a photo with a caption."},
    "q_date": {
        "ru": "📅 <b>Желаемая дата</b>\nВыберите день или напишите дату (ДД.ММ.ГГГГ):",
        "uz": "📅 <b>Qulay sana</b>\nKunni tanlang yoki sanani yozing (KK.OO.YYYY):",
        "en": "📅 <b>Preferred date</b>\nPick a day or type a date (DD.MM.YYYY):"},
    "q_location": {
        "ru": "🗺 <b>Где находится машина?</b>\n\nНажмите «📍 Отправить геолокацию» внизу экрана — мастер приедет по этой точке.\nИли напишите адрес / ориентир: трасса, км, заправка…",
        "uz": "🗺 <b>Mashina qayerda?</b>\n\nEkran pastidagi «📍 Geolokatsiyani yuborish» tugmasini bosing — usta shu nuqtaga keladi.\nYoki manzil / mo‘ljal yozing: trassa, km, yoqilg‘i shoxobchasi…",
        "en": "🗺 <b>Where is the truck?</b>\n\nTap “📍 Send location” at the bottom — the mechanic will come to that point.\nOr type an address / landmark: highway, km, gas station…"},
    "q_photos": {
        "ru": "📷 Отправьте фото неисправности (можно альбомом). Ещё можно: <b>{left}</b>",
        "uz": "📷 Nosozlik rasmlarini yuboring (albom ham mumkin). Yana mumkin: <b>{left}</b>",
        "en": "📷 Send photos of the problem (an album is fine). Remaining: <b>{left}</b>"},
    "photo_added": {"ru": "📷 Фото добавлено ({n}/3)", "uz": "📷 Rasm qo‘shildi ({n}/3)", "en": "📷 Photo added ({n}/3)"},
    "photos_full": {"ru": "📷 Уже добавлено 3 фото.", "uz": "📷 3 ta rasm allaqachon qo‘shilgan.", "en": "📷 3 photos already added."},
    "lbl_car_desc": {"ru": "📋 Описание", "uz": "📋 Tavsif", "en": "📋 Details"},
    "lbl_date": {"ru": "📅 Желаемая дата", "uz": "📅 Qulay sana", "en": "📅 Preferred date"},

    # ---------- request card ----------
    "lbl_car": {"ru": "🚛 Грузовик", "uz": "🚛 Yuk mashinasi", "en": "🚛 Truck"},
    "lbl_year": {"ru": "📅 Год", "uz": "📅 Yil", "en": "📅 Year"},
    "lbl_plate": {"ru": "🔢 Госномер", "uz": "🔢 Davlat raqami", "en": "🔢 Plate"},
    "lbl_service": {"ru": "🔧 Услуга", "uz": "🔧 Xizmat", "en": "🔧 Service"},
    "lbl_problem": {"ru": "⚠️ Проблема", "uz": "⚠️ Muammo", "en": "⚠️ Problem"},
    "lbl_client": {"ru": "👤 Клиент", "uz": "👤 Mijoz", "en": "👤 Client"},
    "lbl_phone": {"ru": "📞 Телефон", "uz": "📞 Telefon", "en": "📞 Phone"},
    "lbl_status": {"ru": "📊 Статус", "uz": "📊 Holat", "en": "📊 Status"},
    "lbl_master": {"ru": "👨‍🔧 Мастер", "uz": "👨‍🔧 Usta", "en": "👨‍🔧 Mechanic"},
    "lbl_ready": {"ru": "⏰ Готовность", "uz": "⏰ Tayyor bo‘lish vaqti", "en": "⏰ Ready by"},
    "lbl_created": {"ru": "🕐 Создана", "uz": "🕐 Yaratilgan", "en": "🕐 Created"},
    "req_title": {"ru": "🎫 <b>Заявка №{number}</b>", "uz": "🎫 <b>Ariza №{number}</b>", "en": "🎫 <b>Request №{number}</b>"},
    "no_requests": {
        "ru": "📭 У вас пока нет заявок.\nНажмите «🔧 Записать грузовик на ремонт», чтобы создать первую.",
        "uz": "📭 Sizda hali arizalar yo‘q.\nBirinchisini yaratish uchun «🔧 Yuk mashinasini ta’mirga yozish» ni bosing.",
        "en": "📭 You have no requests yet.\nTap “🔧 Book a truck repair” to create one."},
    "my_requests_title": {"ru": "📦 <b>Мои заявки</b>", "uz": "📦 <b>Arizalarim</b>", "en": "📦 <b>My requests</b>"},
    "btn_history": {"ru": "📜 История", "uz": "📜 Tarix", "en": "📜 History"},
    "btn_cancel_request": {"ru": "❌ Отменить заявку", "uz": "❌ Arizani bekor qilish", "en": "❌ Cancel request"},
    "cancel_confirm": {
        "ru": "❓ Точно отменить заявку №{number}?", "uz": "❓ №{number} arizani bekor qilasizmi?", "en": "❓ Cancel request №{number}?"},
    "cannot_cancel": {
        "ru": "⚠️ Заявку уже нельзя отменить — свяжитесь с сервисом.",
        "uz": "⚠️ Arizani endi bekor qilib bo‘lmaydi — servis bilan bog‘laning.",
        "en": "⚠️ This request can no longer be cancelled — please contact us."},
    "history_title": {"ru": "📜 <b>История заявки №{number}</b>", "uz": "📜 <b>№{number} ariza tarixi</b>", "en": "📜 <b>History of request №{number}</b>"},
    "h_created": {"ru": "заявка создана", "uz": "ariza yaratildi", "en": "request created"},
    "h_status": {"ru": "статус → {d}", "uz": "holat → {d}", "en": "status → {d}"},
    "h_assigned": {"ru": "назначен мастер: {d}", "uz": "usta tayinlandi: {d}", "en": "mechanic assigned: {d}"},
    "h_master_accepted": {"ru": "мастер принял работу", "uz": "usta ishni qabul qildi", "en": "mechanic accepted the job"},
    "h_ready_at": {"ru": "время готовности: {d}", "uz": "tayyor bo‘lish vaqti: {d}", "en": "ready time: {d}"},
    "h_comment": {"ru": "комментарий: {d}", "uz": "izoh: {d}", "en": "comment: {d}"},
    "h_edited": {"ru": "изменено: {d}", "uz": "o‘zgartirildi: {d}", "en": "edited: {d}"},
    "h_message": {"ru": "сообщение: {d}", "uz": "xabar: {d}", "en": "message: {d}"},
    "role_client": {"ru": "клиент", "uz": "mijoz", "en": "client"},
    "role_master": {"ru": "мастер", "uz": "usta", "en": "mechanic"},
    "role_owner": {"ru": "владелец", "uz": "egasi", "en": "owner"},
    "role_system": {"ru": "система", "uz": "tizim", "en": "system"},
    "role_blocked": {"ru": "заблокирован", "uz": "bloklangan", "en": "blocked"},

    # ---------- statuses ----------
    "st_new": {"ru": "Новая", "uz": "Yangi", "en": "New"},
    "st_accepted": {"ru": "Принята", "uz": "Qabul qilindi", "en": "Accepted"},
    "st_assigned": {"ru": "Назначен мастер", "uz": "Usta tayinlandi", "en": "Mechanic assigned"},
    "st_diagnostics": {"ru": "Диагностика", "uz": "Diagnostika", "en": "Diagnostics"},
    "st_repair": {"ru": "Ремонт", "uz": "Ta’mirlash", "en": "Repair"},
    "st_waiting_parts": {"ru": "Ожидает запчасти", "uz": "Ehtiyot qism kutilmoqda", "en": "Waiting for parts"},
    "st_ready": {"ru": "Готово", "uz": "Tayyor", "en": "Ready"},
    "st_delivered": {"ru": "Грузовик выдан", "uz": "Yuk mashinasi topshirildi", "en": "Truck handed over"},
    "st_cancelled": {"ru": "Отменена", "uz": "Bekor qilindi", "en": "Cancelled"},

    # ---------- services ----------
    "svc_comp_diag": {"ru": "Компьютерная диагностика", "uz": "Kompyuter diagnostikasi", "en": "Computer diagnostics"},
    "svc_engine": {"ru": "Ремонт двигателя (дизель)", "uz": "Dvigatel ta’miri (dizel)", "en": "Engine repair (diesel)"},
    "svc_fuel": {"ru": "Топливная система, форсунки, ТНВД", "uz": "Yoqilg‘i tizimi, forsunka, TNVD", "en": "Fuel system, injectors, pump"},
    "svc_gearbox": {"ru": "КПП и сцепление", "uz": "Uzatmalar qutisi va ilashish", "en": "Gearbox & clutch"},
    "svc_chassis": {"ru": "Ходовая и подвеска, рессоры", "uz": "Yurish qismi, osma, ressorlar", "en": "Suspension & leaf springs"},
    "svc_brakes": {"ru": "Тормозная система (пневматика)", "uz": "Tormoz tizimi (pnevmatika)", "en": "Air brake system"},
    "svc_electric": {"ru": "Автоэлектрика", "uz": "Avtoelektrika", "en": "Electrics"},
    "svc_oil": {"ru": "ТО и замена масла", "uz": "TXK va moy almashtirish", "en": "Service & oil change"},
    "svc_tires": {"ru": "Грузовой шиномонтаж", "uz": "Yuk shinomontaji", "en": "Truck tyre service"},
    "svc_ecology": {"ru": "AdBlue / DPF / EGR", "uz": "AdBlue / DPF / EGR", "en": "AdBlue / DPF / EGR"},
    "svc_ac": {"ru": "Кондиционер и отопитель", "uz": "Konditsioner va isitgich", "en": "A/C & cab heater"},
    "svc_car_diag": {"ru": "Диагностика грузовика", "uz": "Yuk mashinasi diagnostikasi", "en": "Truck inspection"},
    "svc_other": {"ru": "Другое", "uz": "Boshqa", "en": "Other"},

    # ---------- notifications ----------
    "n_new_staff": {
        "ru": "{urgent}🚨 <b>НОВАЯ ЗАЯВКА</b>\n🎫 №{number}\n\n{card}",
        "uz": "{urgent}🚨 <b>YANGI ARIZA</b>\n🎫 №{number}\n\n{card}",
        "en": "{urgent}🚨 <b>NEW REQUEST</b>\n🎫 №{number}\n\n{card}"},
    "btn_accept": {"ru": "✅ Принять", "uz": "✅ Qabul qilish", "en": "✅ Accept"},
    "btn_assign_master": {"ru": "👨‍🔧 Назначить мастера", "uz": "👨‍🔧 Usta tayinlash", "en": "👨‍🔧 Assign mechanic"},
    "btn_call_client": {"ru": "📞 Позвонить клиенту", "uz": "📞 Mijozga qo‘ng‘iroq", "en": "📞 Call client"},
    "cn_header": {"ru": "🔔 Заявка №{number}", "uz": "🔔 Ariza №{number}", "en": "🔔 Request №{number}"},
    "cn_accepted": {
        "ru": "📋 <b>Ваша заявка принята</b>\n№{number}\n\nМы получили вашу заявку и скоро свяжемся с вами.",
        "uz": "📋 <b>Arizangiz qabul qilindi</b>\n№{number}\n\nArizangizni oldik, tez orada siz bilan bog‘lanamiz.",
        "en": "📋 <b>Your request has been accepted</b>\n№{number}\n\nWe have received your request and will contact you soon."},
    "cn_assigned": {
        "ru": "👨‍🔧 <b>Мастер назначен</b>\nЗаявка №{number}\n\nВаш грузовик передан специалисту: <b>{master}</b>.",
        "uz": "👨‍🔧 <b>Usta tayinlandi</b>\nAriza №{number}\n\nYuk mashinangiz mutaxassisga topshirildi: <b>{master}</b>.",
        "en": "👨‍🔧 <b>Mechanic assigned</b>\nRequest №{number}\n\nYour truck has been handed to a specialist: <b>{master}</b>."},
    "cn_diagnostics": {
        "ru": "🔍 <b>Диагностика начата</b>\nЗаявка №{number}\n\nМастер проводит диагностику грузовика.",
        "uz": "🔍 <b>Diagnostika boshlandi</b>\nAriza №{number}\n\nUsta yuk mashinasini diagnostika qilmoqda.",
        "en": "🔍 <b>Diagnostics started</b>\nRequest №{number}\n\nThe mechanic is diagnosing your truck."},
    "cn_repair": {
        "ru": "🔧 <b>Ремонт начат</b>\nЗаявка №{number}\n\nМастер приступил к работе.",
        "uz": "🔧 <b>Ta’mirlash boshlandi</b>\nAriza №{number}\n\nUsta ishga kirishdi.",
        "en": "🔧 <b>Repair started</b>\nRequest №{number}\n\nThe mechanic has started working."},
    "cn_waiting_parts": {
        "ru": "⏰ <b>Ожидаем запчасти</b>\nЗаявка №{number}\n\nРемонт продолжится после поступления запчастей.",
        "uz": "⏰ <b>Ehtiyot qismlar kutilmoqda</b>\nAriza №{number}\n\nEhtiyot qismlar kelgach ta’mirlash davom etadi.",
        "en": "⏰ <b>Waiting for parts</b>\nRequest №{number}\n\nRepair will continue once the parts arrive."},
    "cn_ready": {
        "ru": "🎉 <b>ВАШ ГРУЗОВИК ГОТОВ!</b>\nЗаявка №{number}\n\nМожно забрать грузовик.\n📍 {address}",
        "uz": "🎉 <b>YUK MASHINANGIZ TAYYOR!</b>\nAriza №{number}\n\nYuk mashinasini olib ketishingiz mumkin.\n📍 {address}",
        "en": "🎉 <b>YOUR TRUCK IS READY!</b>\nRequest №{number}\n\nYou can pick up your truck.\n📍 {address}"},
    "cn_delivered": {
        "ru": "🚛 <b>Грузовик выдан</b>\nЗаявка №{number}\n\nСпасибо, что выбрали NAJOT SERVIS! Счастливого пути 🙌",
        "uz": "🚛 <b>Yuk mashinasi topshirildi</b>\nAriza №{number}\n\nNAJOT SERVISni tanlaganingiz uchun rahmat! Oq yo‘l 🙌",
        "en": "🚛 <b>Truck handed over</b>\nRequest №{number}\n\nThank you for choosing NAJOT SERVIS! Drive safe 🙌"},
    "cn_cancelled": {
        "ru": "❌ <b>Заявка отменена</b>\n№{number}", "uz": "❌ <b>Ariza bekor qilindi</b>\n№{number}", "en": "❌ <b>Request cancelled</b>\n№{number}"},
    "cn_new": {
        "ru": "🟡 Заявка №{number} снова в статусе «Новая».", "uz": "🟡 №{number} ariza yana «Yangi» holatida.", "en": "🟡 Request №{number} is back to “New”."},
    "cn_ready_time": {
        "ru": "🔧 <b>Обновление по вашей заявке №{number}</b>\n\nМастер указал ориентировочное время готовности:\n⏰ <b>{when}</b>",
        "uz": "🔧 <b>№{number} arizangiz bo‘yicha yangilik</b>\n\nUsta taxminiy tayyor bo‘lish vaqtini ko‘rsatdi:\n⏰ <b>{when}</b>",
        "en": "🔧 <b>Update on your request №{number}</b>\n\nThe mechanic set the estimated ready time:\n⏰ <b>{when}</b>"},
    "cn_comment": {
        "ru": "💬 <b>Комментарий мастера</b> по заявке №{number}:\n\n{text}",
        "uz": "💬 №{number} ariza bo‘yicha <b>usta izohi</b>:\n\n{text}",
        "en": "💬 <b>Mechanic’s comment</b> on request №{number}:\n\n{text}"},

    # ---------- chat with master ----------
    "cm_choose": {
        "ru": "💬 По какой заявке хотите написать?", "uz": "💬 Qaysi ariza bo‘yicha yozmoqchisiz?", "en": "💬 Which request is your message about?"},
    "cm_write": {
        "ru": "✍️ Напишите сообщение по заявке №{number}. Мастер получит его сразу.",
        "uz": "✍️ №{number} ariza bo‘yicha xabar yozing. Usta uni darhol oladi.",
        "en": "✍️ Write your message about request №{number}. The mechanic will get it right away."},
    "cm_no_active": {
        "ru": "📭 Нет активных заявок. Чтобы связаться с сервисом, нажмите «📞 Позвонить» или создайте заявку.",
        "uz": "📭 Faol arizalar yo‘q. Servis bilan bog‘lanish uchun «📞 Qo‘ng‘iroq qilish» ni bosing yoki ariza yarating.",
        "en": "📭 No active requests. Tap “📞 Call us” or create a request."},
    "cm_sent": {"ru": "✅ Сообщение отправлено. Ответ придёт сюда.", "uz": "✅ Xabar yuborildi. Javob shu yerga keladi.", "en": "✅ Message sent. The reply will arrive here."},
    "msg_from_client": {
        "ru": "💬 <b>Сообщение от клиента</b>\n🎫 №{number} · {name} · {phone}\n\n{text}",
        "uz": "💬 <b>Mijozdan xabar</b>\n🎫 №{number} · {name} · {phone}\n\n{text}",
        "en": "💬 <b>Message from client</b>\n🎫 №{number} · {name} · {phone}\n\n{text}"},
    "btn_reply": {"ru": "↩️ Ответить", "uz": "↩️ Javob berish", "en": "↩️ Reply"},
    "reply_write": {"ru": "✍️ Напишите ответ клиенту (заявка №{number}):", "uz": "✍️ Mijozga javob yozing (ariza №{number}):", "en": "✍️ Write your reply to the client (request №{number}):"},
    "msg_from_service": {
        "ru": "💬 <b>Ответ NAJOT SERVIS</b> по заявке №{number}\n👨‍🔧 {name}:\n\n{text}",
        "uz": "💬 №{number} ariza bo‘yicha <b>NAJOT SERVIS javobi</b>\n👨‍🔧 {name}:\n\n{text}",
        "en": "💬 <b>NAJOT SERVIS reply</b> on request №{number}\n👨‍🔧 {name}:\n\n{text}"},
    "reply_sent": {"ru": "✅ Ответ отправлен клиенту.", "uz": "✅ Javob mijozga yuborildi.", "en": "✅ Reply sent to the client."},
    "client_unreachable": {
        "ru": "⚠️ У клиента нет Telegram-аккаунта в системе — позвоните: {phone}",
        "uz": "⚠️ Mijozning tizimda Telegram akkaunti yo‘q — qo‘ng‘iroq qiling: {phone}",
        "en": "⚠️ The client has no Telegram account in the system — call: {phone}"},

    # ---------- trucks ----------
    "cars_title": {"ru": "🚛 <b>Мои грузовики</b>", "uz": "🚛 <b>Mening yuk mashinalarim</b>", "en": "🚛 <b>My trucks</b>"},
    "cars_empty": {
        "ru": "У вас пока нет сохранённых грузовиков.", "uz": "Sizda hali saqlangan yuk mashinalari yo‘q.", "en": "You have no saved trucks yet."},
    "btn_add_car": {"ru": "➕ Добавить грузовик", "uz": "➕ Yuk mashinasi qo‘shish", "en": "➕ Add a truck"},
    "car_brand": {"ru": "🚛 Выберите марку или напишите название:", "uz": "🚛 Markani tanlang yoki nomini yozing:", "en": "🚛 Choose the brand or type its name:"},
    "car_model": {"ru": "🚚 Марка: <b>{brand}</b>\nВведите модель:", "uz": "🚚 Marka: <b>{brand}</b>\nModelni kiriting:", "en": "🚚 Brand: <b>{brand}</b>\nEnter the model:"},
    "car_year": {"ru": "📅 Введите год выпуска:", "uz": "📅 Ishlab chiqarilgan yilni kiriting:", "en": "📅 Enter the year:"},
    "car_plate": {"ru": "🔢 Введите госномер (например 01A123BC):", "uz": "🔢 Davlat raqamini kiriting (masalan 01A123BC):", "en": "🔢 Enter the plate number (e.g. 01A123BC):"},
    "car_vin": {"ru": "🔑 Введите VIN (необязательно):", "uz": "🔑 VIN kiriting (ixtiyoriy):", "en": "🔑 Enter VIN (optional):"},
    "car_bad_plate": {"ru": "⚠️ Госномер: 4–12 символов, буквы и цифры.", "uz": "⚠️ Davlat raqami: 4–12 belgi, harf va raqamlar.", "en": "⚠️ Plate: 4–12 letters/digits."},
    "car_bad_vin": {"ru": "⚠️ VIN должен содержать 17 символов.", "uz": "⚠️ VIN 17 belgidan iborat bo‘lishi kerak.", "en": "⚠️ VIN must be 17 characters."},
    "car_saved": {"ru": "✅ Грузовик сохранён!", "uz": "✅ Yuk mashinasi saqlandi!", "en": "✅ Truck saved!"},
    "car_deleted": {"ru": "🗑 Грузовик удалён.", "uz": "🗑 Yuk mashinasi o‘chirildi.", "en": "🗑 Truck deleted."},
    "car_limit": {"ru": "⚠️ Можно сохранить не более {n} грузовиков.", "uz": "⚠️ Ko‘pi bilan {n} ta yuk mashinasi saqlash mumkin.", "en": "⚠️ You can save up to {n} trucks."},
    "btn_delete_car": {"ru": "🗑 Удалить", "uz": "🗑 O‘chirish", "en": "🗑 Delete"},
    "btn_book_with_car": {"ru": "🔧 Записать этот грузовик", "uz": "🔧 Shu yuk mashinasini yozish", "en": "🔧 Book this truck"},
    "car_card": {
        "ru": "🚛 <b>{brand} {model}</b>\n🚚 Тип: {body}\n📅 Год: {year}\n🔢 Госномер: {plate}\n🔑 VIN: {vin}",
        "uz": "🚛 <b>{brand} {model}</b>\n🚚 Turi: {body}\n📅 Yil: {year}\n🔢 Davlat raqami: {plate}\n🔑 VIN: {vin}",
        "en": "🚛 <b>{brand} {model}</b>\n🚚 Type: {body}\n📅 Year: {year}\n🔢 Plate: {plate}\n🔑 VIN: {vin}"},

    # ---------- master ----------
    "m_menu": {
        "ru": "👨‍🔧 <b>Панель мастера</b> · {name}\n\n🔔 Новые: <b>{new}</b>   🔧 В работе: <b>{work}</b>",
        "uz": "👨‍🔧 <b>Usta paneli</b> · {name}\n\n🔔 Yangi: <b>{new}</b>   🔧 Jarayonda: <b>{work}</b>",
        "en": "👨‍🔧 <b>Mechanic panel</b> · {name}\n\n🔔 New: <b>{new}</b>   🔧 In progress: <b>{work}</b>"},
    "btn_m_new": {"ru": "🔔 Новые задания", "uz": "🔔 Yangi topshiriqlar", "en": "🔔 New jobs"},
    "btn_m_work": {"ru": "🔧 Мои работы", "uz": "🔧 Mening ishlarim", "en": "🔧 My jobs"},
    "btn_m_deadlines": {"ru": "⏰ Срок выполнения", "uz": "⏰ Bajarish muddati", "en": "⏰ Deadlines"},
    "btn_m_history": {"ru": "📋 История", "uz": "📋 Tarix", "en": "📋 History"},
    "btn_m_profile": {"ru": "👤 Профиль", "uz": "👤 Profil", "en": "👤 Profile"},
    "m_empty": {"ru": "📭 Здесь пока пусто.", "uz": "📭 Hozircha bo‘sh.", "en": "📭 Nothing here yet."},
    "m_deadlines_title": {"ru": "⏰ <b>Сроки выполнения</b>", "uz": "⏰ <b>Bajarish muddatlari</b>", "en": "⏰ <b>Deadlines</b>"},
    "m_no_deadline": {"ru": "срок не указан", "uz": "muddat ko‘rsatilmagan", "en": "no deadline"},
    "m_overdue": {"ru": "🔴 просрочено", "uz": "🔴 muddati o‘tgan", "en": "🔴 overdue"},
    "btn_m_accept": {"ru": "✅ Принять работу", "uz": "✅ Ishni qabul qilish", "en": "✅ Accept job"},
    "btn_m_diag": {"ru": "🔍 Начать диагностику", "uz": "🔍 Diagnostikani boshlash", "en": "🔍 Start diagnostics"},
    "btn_m_repair": {"ru": "🔧 Начать ремонт", "uz": "🔧 Ta’mirni boshlash", "en": "🔧 Start repair"},
    "btn_m_parts": {"ru": "⏳ Ждём запчасти", "uz": "⏳ Ehtiyot qism kutilmoqda", "en": "⏳ Waiting for parts"},
    "btn_m_ready_time": {"ru": "⏰ Указать время готовности", "uz": "⏰ Tayyor bo‘lish vaqtini ko‘rsatish", "en": "⏰ Set ready time"},
    "btn_m_comment": {"ru": "📝 Добавить комментарий", "uz": "📝 Izoh qo‘shish", "en": "📝 Add comment"},
    "btn_m_finish": {"ru": "✅ Завершить ремонт", "uz": "✅ Ta’mirni yakunlash", "en": "✅ Finish repair"},
    "m_profile": {
        "ru": "👤 <b>Профиль мастера</b>\n\nИмя: <b>{name}</b>\nСпециализация: {spec}\n\n🔧 В работе: {work}\n✅ Выполнено всего: {done}\n✅ За 30 дней: {done30}",
        "uz": "👤 <b>Usta profili</b>\n\nIsm: <b>{name}</b>\nMutaxassislik: {spec}\n\n🔧 Jarayonda: {work}\n✅ Jami bajarilgan: {done}\n✅ 30 kunda: {done30}",
        "en": "👤 <b>Mechanic profile</b>\n\nName: <b>{name}</b>\nSpecialization: {spec}\n\n🔧 In progress: {work}\n✅ Completed total: {done}\n✅ Last 30 days: {done30}"},
    "m_new_job": {
        "ru": "🔔 <b>Новое задание!</b>\n\n{card}", "uz": "🔔 <b>Yangi topshiriq!</b>\n\n{card}", "en": "🔔 <b>New job!</b>\n\n{card}"},
    "m_take_offer": {
        "ru": "🔔 <b>Новая заявка — кто возьмёт?</b>\n\n{card}", "uz": "🔔 <b>Yangi ariza — kim oladi?</b>\n\n{card}",
        "en": "🔔 <b>New request — who takes it?</b>\n\n{card}"},
    "btn_take": {"ru": "🙋 Взять заявку", "uz": "🙋 Arizani olish", "en": "🙋 Take the job"},
    "take_ok": {"ru": "✅ Заявка ваша!", "uz": "✅ Ariza sizniki!", "en": "✅ The job is yours!"},
    "take_taken": {"ru": "⚠️ Эту заявку уже взял другой мастер.", "uz": "⚠️ Bu arizani boshqa usta oldi.",
                   "en": "⚠️ Another mechanic already took this job."},
    "m_job_removed": {
        "ru": "ℹ️ Заявка №{number} снята с вас.", "uz": "ℹ️ №{number} ariza sizdan olindi.", "en": "ℹ️ Request №{number} was unassigned from you."},
    "staff_update": {
        "ru": "ℹ️ №{number}: {what} · {who}", "uz": "ℹ️ №{number}: {what} · {who}", "en": "ℹ️ №{number}: {what} · {who}"},
    "rt_date": {
        "ru": "⏰ <b>Когда грузовик будет готов?</b>\n\n📅 Выберите дату или введите её (ДД.ММ.ГГГГ):",
        "uz": "⏰ <b>Yuk mashinasi qachon tayyor bo‘ladi?</b>\n\n📅 Sanani tanlang yoki kiriting (KK.OO.YYYY):",
        "en": "⏰ <b>When will the truck be ready?</b>\n\n📅 Pick a date or type it (DD.MM.YYYY):"},
    "rt_today": {"ru": "Сегодня", "uz": "Bugun", "en": "Today"},
    "rt_tomorrow": {"ru": "Завтра", "uz": "Ertaga", "en": "Tomorrow"},
    "rt_time": {
        "ru": "📅 Дата: <b>{date}</b>\n\n🕐 Выберите время или введите его (ЧЧ:ММ):",
        "uz": "📅 Sana: <b>{date}</b>\n\n🕐 Vaqtni tanlang yoki kiriting (SS:DD):",
        "en": "📅 Date: <b>{date}</b>\n\n🕐 Pick a time or type it (HH:MM):"},
    "rt_bad_date": {"ru": "⚠️ Неверная дата. Пример: 03.10.2026", "uz": "⚠️ Noto‘g‘ri sana. Namuna: 03.10.2026", "en": "⚠️ Invalid date. Example: 03.10.2026"},
    "rt_bad_time": {"ru": "⚠️ Неверное время. Пример: 18:30", "uz": "⚠️ Noto‘g‘ri vaqt. Namuna: 18:30", "en": "⚠️ Invalid time. Example: 18:30"},
    "rt_past": {"ru": "⚠️ Это время уже прошло.", "uz": "⚠️ Bu vaqt allaqachon o‘tgan.", "en": "⚠️ That time is in the past."},
    "rt_saved": {
        "ru": "🕐 Грузовик будет готов:\n<b>{when}</b>\n\n✅ Клиент уведомлён.",
        "uz": "🕐 Yuk mashinasi tayyor bo‘ladi:\n<b>{when}</b>\n\n✅ Mijozga xabar yuborildi.",
        "en": "🕐 The truck will be ready:\n<b>{when}</b>\n\n✅ The client has been notified."},
    "comment_write": {"ru": "📝 Напишите комментарий (клиент его увидит):", "uz": "📝 Izoh yozing (mijoz uni ko‘radi):", "en": "📝 Write a comment (the client will see it):"},
    "comment_saved": {"ru": "✅ Комментарий сохранён и отправлен клиенту.", "uz": "✅ Izoh saqlandi va mijozga yuborildi.", "en": "✅ Comment saved and sent to the client."},
    "done_ok": {"ru": "✅ Готово.", "uz": "✅ Bajarildi.", "en": "✅ Done."},
    "cl_sent": {"ru": "📨 Клиент уведомлён в Telegram", "uz": "📨 Mijozga Telegramda xabar yuborildi",
                "en": "📨 Client notified in Telegram"},
    "cl_failed": {"ru": "⚠️ Не удалось отправить клиенту (заблокировал бота?). Позвоните: {phone}",
                  "uz": "⚠️ Mijozga yuborib bo‘lmadi (botni bloklaganmi?). Qo‘ng‘iroq qiling: {phone}",
                  "en": "⚠️ Could not message the client (bot blocked?). Call: {phone}"},
    "cl_no_client": {"ru": "⚠️ Клиента нет в Telegram-боте (заявка создана вручную). Позвоните: {phone}",
                     "uz": "⚠️ Mijoz Telegram-botda yo‘q (ariza qo‘lda yaratilgan). Qo‘ng‘iroq qiling: {phone}",
                     "en": "⚠️ The client isn’t in the Telegram bot (manual request). Call: {phone}"},
    "status_changed": {"ru": "✅ Статус: {status}", "uz": "✅ Holat: {status}", "en": "✅ Status: {status}"},

    # ---------- owner ----------
    "o_menu": {
        "ru": "👑 <b>Панель управления NAJOT SERVIS</b>\n\n🆕 Новых: <b>{new}</b>\n🔧 В работе: <b>{work}</b>\n✅ Готово к выдаче: <b>{ready}</b>\n📅 Сегодня: <b>{today}</b>",
        "uz": "👑 <b>NAJOT SERVIS boshqaruv paneli</b>\n\n🆕 Yangi: <b>{new}</b>\n🔧 Jarayonda: <b>{work}</b>\n✅ Topshirishga tayyor: <b>{ready}</b>\n📅 Bugun: <b>{today}</b>",
        "en": "👑 <b>NAJOT SERVIS control panel</b>\n\n🆕 New: <b>{new}</b>\n🔧 In progress: <b>{work}</b>\n✅ Ready for pickup: <b>{ready}</b>\n📅 Today: <b>{today}</b>"},
    "btn_o_all": {"ru": "📋 Все заявки", "uz": "📋 Barcha arizalar", "en": "📋 All requests"},
    "btn_o_new": {"ru": "🆕 Новые", "uz": "🆕 Yangi", "en": "🆕 New"},
    "btn_o_work": {"ru": "🔧 В работе", "uz": "🔧 Jarayonda", "en": "🔧 In progress"},
    "btn_o_done": {"ru": "✅ Завершённые", "uz": "✅ Yakunlangan", "en": "✅ Completed"},
    "btn_o_cancelled": {"ru": "❌ Отменённые", "uz": "❌ Bekor qilingan", "en": "❌ Cancelled"},
    "btn_o_masters": {"ru": "👨‍🔧 Мастера", "uz": "👨‍🔧 Ustalar", "en": "👨‍🔧 Mechanics"},
    "btn_o_clients": {"ru": "👥 Клиенты", "uz": "👥 Mijozlar", "en": "👥 Clients"},
    "btn_o_cars": {"ru": "🚛 Грузовики", "uz": "🚛 Yuk mashinalari", "en": "🚛 Trucks"},
    "btn_o_stats": {"ru": "📈 Статистика", "uz": "📈 Statistika", "en": "📈 Statistics"},
    "btn_o_settings": {"ru": "⚙️ Настройки", "uz": "⚙️ Sozlamalar", "en": "⚙️ Settings"},
    "btn_o_create": {"ru": "➕ Создать заявку", "uz": "➕ Ariza yaratish", "en": "➕ Create request"},
    "btn_o_search": {"ru": "🔎 Найти заявку", "uz": "🔎 Arizani topish", "en": "🔎 Find request"},
    "o_search_ask": {
        "ru": "🔎 Введите номер заявки (NS-000001 или 1), телефон или имя клиента:",
        "uz": "🔎 Ariza raqami (NS-000001 yoki 1), telefon yoki mijoz ismini kiriting:",
        "en": "🔎 Enter request number (NS-000001 or 1), phone or client name:"},
    "list_all": {"ru": "📋 <b>Все заявки</b>", "uz": "📋 <b>Barcha arizalar</b>", "en": "📋 <b>All requests</b>"},
    "list_new": {"ru": "🆕 <b>Новые заявки</b>", "uz": "🆕 <b>Yangi arizalar</b>", "en": "🆕 <b>New requests</b>"},
    "list_work": {"ru": "🔧 <b>В работе</b>", "uz": "🔧 <b>Jarayonda</b>", "en": "🔧 <b>In progress</b>"},
    "list_done": {"ru": "✅ <b>Завершённые</b>", "uz": "✅ <b>Yakunlangan</b>", "en": "✅ <b>Completed</b>"},
    "list_cancelled": {"ru": "❌ <b>Отменённые</b>", "uz": "❌ <b>Bekor qilingan</b>", "en": "❌ <b>Cancelled</b>"},
    "list_search": {"ru": "🔎 <b>Результаты поиска</b>", "uz": "🔎 <b>Qidiruv natijalari</b>", "en": "🔎 <b>Search results</b>"},
    "list_count": {"ru": "Всего: {n} · стр. {p}/{pages}", "uz": "Jami: {n} · {p}/{pages}-sahifa", "en": "Total: {n} · page {p}/{pages}"},
    "btn_o_status": {"ru": "📊 Изменить статус", "uz": "📊 Holatni o‘zgartirish", "en": "📊 Change status"},
    "btn_o_ready": {"ru": "⏰ Дата/время готовности", "uz": "⏰ Tayyor bo‘lish vaqti", "en": "⏰ Ready date/time"},
    "btn_o_edit": {"ru": "✏️ Редактировать", "uz": "✏️ Tahrirlash", "en": "✏️ Edit"},
    "btn_o_delete": {"ru": "🗑 Удалить", "uz": "🗑 O‘chirish", "en": "🗑 Delete"},
    "o_choose_status": {"ru": "📊 Выберите новый статус:", "uz": "📊 Yangi holatni tanlang:", "en": "📊 Choose the new status:"},
    "o_choose_master": {"ru": "👨‍🔧 Выберите мастера:", "uz": "👨‍🔧 Ustani tanlang:", "en": "👨‍🔧 Choose a mechanic:"},
    "o_no_masters": {
        "ru": "⚠️ Мастеров пока нет. Добавьте их в разделе «👨‍🔧 Мастера».",
        "uz": "⚠️ Hali ustalar yo‘q. Ularni «👨‍🔧 Ustalar» bo‘limida qo‘shing.",
        "en": "⚠️ No mechanics yet. Add them in “👨‍🔧 Mechanics”."},
    "btn_unassign": {"ru": "🚫 Снять мастера", "uz": "🚫 Ustani olib tashlash", "en": "🚫 Unassign"},
    "o_assigned_ok": {"ru": "✅ Мастер назначен: {name}", "uz": "✅ Usta tayinlandi: {name}", "en": "✅ Mechanic assigned: {name}"},
    "o_delete_confirm": {
        "ru": "🗑 Удалить заявку №{number} безвозвратно?", "uz": "🗑 №{number} arizani butunlay o‘chirasizmi?", "en": "🗑 Permanently delete request №{number}?"},
    "o_deleted": {"ru": "🗑 Заявка №{number} удалена.", "uz": "🗑 №{number} ariza o‘chirildi.", "en": "🗑 Request №{number} deleted."},
    "o_edit_what": {"ru": "✏️ Какое поле изменить?", "uz": "✏️ Qaysi maydonni o‘zgartiramiz?", "en": "✏️ Which field to edit?"},
    "o_edit_enter": {"ru": "✍️ Введите новое значение для «{field}»:", "uz": "✍️ «{field}» uchun yangi qiymat kiriting:", "en": "✍️ Enter a new value for “{field}”:"},
    "o_edit_saved": {"ru": "✅ Сохранено.", "uz": "✅ Saqlandi.", "en": "✅ Saved."},
    "o_masters_title": {"ru": "👨‍🔧 <b>Мастера</b>", "uz": "👨‍🔧 <b>Ustalar</b>", "en": "👨‍🔧 <b>Mechanics</b>"},
    "btn_add_master": {"ru": "➕ Добавить мастера", "uz": "➕ Usta qo‘shish", "en": "➕ Add mechanic"},
    "o_invite": {
        "ru": "🔗 <b>Приглашение для мастера</b>\n\nОтправьте эту одноразовую ссылку мастеру. После перехода по ней он получит доступ к панели мастера:\n\n<code>{link}</code>",
        "uz": "🔗 <b>Usta uchun taklif</b>\n\nUshbu bir martalik havolani ustaga yuboring. U havolaga o‘tgach usta paneliga kirish huquqini oladi:\n\n<code>{link}</code>",
        "en": "🔗 <b>Mechanic invitation</b>\n\nSend this one-time link to the mechanic. After opening it they get access to the mechanic panel:\n\n<code>{link}</code>"},
    "o_master_card": {
        "ru": "👨‍🔧 <b>{name}</b> {active}\nTelegram: {tg}\nСпециализация: {spec}\n\n🔧 В работе: {work}\n✅ Выполнено: {done}",
        "uz": "👨‍🔧 <b>{name}</b> {active}\nTelegram: {tg}\nMutaxassislik: {spec}\n\n🔧 Jarayonda: {work}\n✅ Bajarilgan: {done}",
        "en": "👨‍🔧 <b>{name}</b> {active}\nTelegram: {tg}\nSpecialization: {spec}\n\n🔧 In progress: {work}\n✅ Completed: {done}"},
    "btn_m_toggle_off": {"ru": "⏸ Деактивировать", "uz": "⏸ O‘chirish", "en": "⏸ Deactivate"},
    "btn_m_toggle_on": {"ru": "▶️ Активировать", "uz": "▶️ Faollashtirish", "en": "▶️ Activate"},
    "btn_m_spec": {"ru": "🏷 Специализация", "uz": "🏷 Mutaxassislik", "en": "🏷 Specialization"},
    "btn_m_jobs": {"ru": "📋 Заявки мастера", "uz": "📋 Usta arizalari", "en": "📋 Mechanic’s jobs"},
    "btn_m_remove": {"ru": "🗑 Удалить из мастеров", "uz": "🗑 Ustalardan o‘chirish", "en": "🗑 Remove mechanic role"},
    "o_spec_enter": {"ru": "🏷 Введите специализацию мастера:", "uz": "🏷 Usta mutaxassisligini kiriting:", "en": "🏷 Enter the specialization:"},
    "inv_ok": {
        "ru": "🎉 Вы добавлены как <b>мастер NAJOT SERVIS</b>!", "uz": "🎉 Siz <b>NAJOT SERVIS ustasi</b> sifatida qo‘shildingiz!", "en": "🎉 You have been added as a <b>NAJOT SERVIS mechanic</b>!"},
    "inv_bad": {"ru": "⚠️ Ссылка-приглашение недействительна или уже использована.", "uz": "⚠️ Taklif havolasi yaroqsiz yoki allaqachon ishlatilgan.", "en": "⚠️ The invitation link is invalid or already used."},
    "inv_used_notify": {"ru": "✅ {name} принял приглашение и стал мастером.", "uz": "✅ {name} taklifni qabul qildi va usta bo‘ldi.", "en": "✅ {name} accepted the invitation and is now a mechanic."},
    "o_users_title": {"ru": "👥 <b>Клиенты и пользователи</b>", "uz": "👥 <b>Mijozlar va foydalanuvchilar</b>", "en": "👥 <b>Clients & users</b>"},
    "o_user_card": {
        "ru": "👤 <b>{name}</b>\nTelegram: {tg} (ID <code>{tg_id}</code>)\n📞 {phone}\nРоль: <b>{role}</b>\nЯзык: {ulang}\n\n📋 Заявок: {reqs}\n🚛 Грузовиков: {cars}\n🕐 Регистрация: {created}",
        "uz": "👤 <b>{name}</b>\nTelegram: {tg} (ID <code>{tg_id}</code>)\n📞 {phone}\nRol: <b>{role}</b>\nTil: {ulang}\n\n📋 Arizalar: {reqs}\n🚛 Yuk mashinalari: {cars}\n🕐 Ro‘yxatdan o‘tgan: {created}",
        "en": "👤 <b>{name}</b>\nTelegram: {tg} (ID <code>{tg_id}</code>)\n📞 {phone}\nRole: <b>{role}</b>\nLanguage: {ulang}\n\n📋 Requests: {reqs}\n🚛 Trucks: {cars}\n🕐 Registered: {created}"},
    "btn_make_master": {"ru": "👨‍🔧 Сделать мастером", "uz": "👨‍🔧 Usta qilish", "en": "👨‍🔧 Make mechanic"},
    "btn_make_client": {"ru": "👤 Сделать клиентом", "uz": "👤 Mijoz qilish", "en": "👤 Make client"},
    "btn_make_owner": {"ru": "👑 Сделать владельцем", "uz": "👑 Egasi qilish", "en": "👑 Make owner"},
    "btn_block": {"ru": "🚫 Заблокировать", "uz": "🚫 Bloklash", "en": "🚫 Block"},
    "btn_unblock": {"ru": "✅ Разблокировать", "uz": "✅ Blokdan chiqarish", "en": "✅ Unblock"},
    "btn_user_requests": {"ru": "📋 Заявки клиента", "uz": "📋 Mijoz arizalari", "en": "📋 Client’s requests"},
    "o_role_changed": {"ru": "✅ Роль изменена: {role}", "uz": "✅ Rol o‘zgartirildi: {role}", "en": "✅ Role changed: {role}"},
    "o_cant_self": {"ru": "⚠️ Нельзя изменить собственную роль.", "uz": "⚠️ O‘z rolingizni o‘zgartirib bo‘lmaydi.", "en": "⚠️ You can’t change your own role."},
    "o_cars_title": {"ru": "🚛 <b>Грузовики клиентов</b>", "uz": "🚛 <b>Mijozlar yuk mashinalarii</b>", "en": "🚛 <b>Client trucks</b>"},
    "stats": {
        "ru": "📈 <b>Статистика NAJOT SERVIS</b>\n\n📋 Всего заявок: <b>{total}</b>\n🆕 Новых: <b>{new}</b>\n🔧 В работе: <b>{work}</b>\n✅ Завершённых: <b>{done}</b>\n❌ Отменённых: <b>{cancelled}</b>\n🆘 Вызовов: <b>{sos}</b>\n\n📅 За сегодня: <b>{today}</b>\n📅 За неделю: <b>{week}</b>\n📅 За месяц: <b>{month}</b>\n\n⏱ Среднее время ремонта: <b>{avg}</b>\n👥 Клиентов: <b>{clients}</b> · 👨‍🔧 Мастеров: <b>{masters}</b>\n\n🏆 <b>Популярные услуги</b>\n{top}\n\n👨‍🔧 <b>Мастера (выполнено)</b>\n{mtop}",
        "uz": "📈 <b>NAJOT SERVIS statistikasi</b>\n\n📋 Jami arizalar: <b>{total}</b>\n🆕 Yangi: <b>{new}</b>\n🔧 Jarayonda: <b>{work}</b>\n✅ Yakunlangan: <b>{done}</b>\n❌ Bekor qilingan: <b>{cancelled}</b>\n🆘 Chaqiruvlar: <b>{sos}</b>\n\n📅 Bugun: <b>{today}</b>\n📅 Hafta: <b>{week}</b>\n📅 Oy: <b>{month}</b>\n\n⏱ O‘rtacha ta’mirlash vaqti: <b>{avg}</b>\n👥 Mijozlar: <b>{clients}</b> · 👨‍🔧 Ustalar: <b>{masters}</b>\n\n🏆 <b>Ommabop xizmatlar</b>\n{top}\n\n👨‍🔧 <b>Ustalar (bajarilgan)</b>\n{mtop}",
        "en": "📈 <b>NAJOT SERVIS statistics</b>\n\n📋 Total requests: <b>{total}</b>\n🆕 New: <b>{new}</b>\n🔧 In progress: <b>{work}</b>\n✅ Completed: <b>{done}</b>\n❌ Cancelled: <b>{cancelled}</b>\n🆘 Call-outs: <b>{sos}</b>\n\n📅 Today: <b>{today}</b>\n📅 This week: <b>{week}</b>\n📅 This month: <b>{month}</b>\n\n⏱ Average repair time: <b>{avg}</b>\n👥 Clients: <b>{clients}</b> · 👨‍🔧 Mechanics: <b>{masters}</b>\n\n🏆 <b>Popular services</b>\n{top}\n\n👨‍🔧 <b>Mechanics (completed)</b>\n{mtop}"},
    "o_settings": {
        "ru": "⚙️ <b>Настройки</b>\n\n📍 Адрес: {address}\n📞 Телефон: {phone}\n💬 Telegram: @{telegram}\n📸 Instagram: @{instagram}\n🕐 Режим работы: {work_hours}\n🗺 Точка: {location}\n\n🔔 Уведомления о новых заявках получают все владельцы{chat}.",
        "uz": "⚙️ <b>Sozlamalar</b>\n\n📍 Manzil: {address}\n📞 Telefon: {phone}\n💬 Telegram: @{telegram}\n📸 Instagram: @{instagram}\n🕐 Ish vaqti: {work_hours}\n🗺 Nuqta: {location}\n\n🔔 Yangi arizalar haqida xabarni barcha egalar oladi{chat}.",
        "en": "⚙️ <b>Settings</b>\n\n📍 Address: {address}\n📞 Phone: {phone}\n💬 Telegram: @{telegram}\n📸 Instagram: @{instagram}\n🕐 Working hours: {work_hours}\n🗺 Pin: {location}\n\n🔔 New request alerts go to all owners{chat}."},
    "set_address": {"ru": "📍 Адрес", "uz": "📍 Manzil", "en": "📍 Address"},
    "set_phone": {"ru": "📞 Телефон", "uz": "📞 Telefon", "en": "📞 Phone"},
    "set_phone2": {"ru": "📞 Телефон 2", "uz": "📞 Telefon 2", "en": "📞 Phone 2"},
    "set_telegram": {"ru": "💬 Telegram", "uz": "💬 Telegram", "en": "💬 Telegram"},
    "set_instagram": {"ru": "📸 Instagram", "uz": "📸 Instagram", "en": "📸 Instagram"},
    "set_work_hours": {"ru": "🕐 Режим работы", "uz": "🕐 Ish vaqti", "en": "🕐 Working hours"},
    "owner_ok": {"ru": "👑 Вы назначены владельцем NAJOT SERVIS.", "uz": "👑 Siz NAJOT SERVIS egasi etib tayinlandingiz.", "en": "👑 You are now an owner of NAJOT SERVIS."},
    "owner_bad": {"ru": "⛔ Неверный код.", "uz": "⛔ Noto‘g‘ri kod.", "en": "⛔ Wrong code."},

    # ---------- AI ----------
    "ai_intro": {
        "ru": "🤖 <b>AI-помощник NAJOT SERVIS</b>\n\nОпишите, что происходит с грузовиком — например: «Машина не заводится». Я задам несколько уточняющих вопросов и помогу оформить заявку мастеру.\n\n<i>Я не ставлю диагноз — точную причину определит специалист.</i>",
        "uz": "🤖 <b>NAJOT SERVIS AI-yordamchisi</b>\n\nYuk mashinasi bilan nima bo‘layotganini yozing — masalan: «Mashina o‘t olmayapti». Men bir nechta savol beraman va ustaga ariza tuzishga yordam beraman.\n\n<i>Men tashxis qo‘ymayman — aniq sababni mutaxassis aniqlaydi.</i>",
        "en": "🤖 <b>NAJOT SERVIS AI assistant</b>\n\nDescribe what is happening with your truck — e.g. “The truck won’t start”. I’ll ask a few questions and help you create a request for a mechanic.\n\n<i>I don’t diagnose — a specialist will determine the exact cause.</i>"},
    "btn_ai_book": {"ru": "📝 Создать заявку", "uz": "📝 Ariza yaratish", "en": "📝 Create request"},
    "btn_ai_end": {"ru": "✖️ Завершить чат", "uz": "✖️ Suhbatni tugatish", "en": "✖️ End chat"},
    "ai_ready": {
        "ru": "\n\n✅ Информации достаточно. Нажмите «📝 Создать заявку» — данные подставятся автоматически.",
        "uz": "\n\n✅ Ma’lumot yetarli. «📝 Ariza yaratish» ni bosing — ma’lumotlar avtomatik to‘ldiriladi.",
        "en": "\n\n✅ That’s enough information. Tap “📝 Create request” — the details will be filled in automatically."},
    "ai_unavailable": {
        "ru": "⚠️ AI временно недоступен. Продолжим в упрощённом режиме.",
        "uz": "⚠️ AI vaqtincha ishlamayapti. Soddalashtirilgan rejimda davom etamiz.",
        "en": "⚠️ AI is temporarily unavailable. Let’s continue in simple mode."},
    "ai_q_brand": {"ru": "🚛 Какая марка грузовика?", "uz": "🚛 Yuk mashinasi markasi qanday?", "en": "🚛 What is the truck brand?"},
    "ai_q_model": {"ru": "🚚 Какая модель?", "uz": "🚚 Qaysi model?", "en": "🚚 Which model?"},
    "ai_q_year": {"ru": "📅 Какой год выпуска?", "uz": "📅 Ishlab chiqarilgan yili?", "en": "📅 What year?"},
    "ai_q_symptoms": {
        "ru": "⚠️ Опишите симптомы подробнее: что именно происходит (звуки, запахи, лампочки на панели)?",
        "uz": "⚠️ Belgilarni batafsil yozing: aniq nima bo‘lyapti (ovozlar, hidlar, paneldagi chiroqlar)?",
        "en": "⚠️ Describe the symptoms: what exactly happens (noises, smells, dashboard lights)?"},
    "ai_q_since": {"ru": "🕐 Когда появилась проблема?", "uz": "🕐 Muammo qachon paydo bo‘ldi?", "en": "🕐 When did the problem start?"},
    "ai_q_extra": {
        "ru": "➕ Есть ли дополнительные признаки? (если нет — напишите «нет»)",
        "uz": "➕ Qo‘shimcha belgilar bormi? (yo‘q bo‘lsa — «yo‘q» deb yozing)",
        "en": "➕ Any additional signs? (if none, type “no”)"},
    "ai_summary": {
        "ru": "📝 <b>Итог для мастера</b>\n\n🚛 {truck}, {year}\n⚠️ {problem}",
        "uz": "📝 <b>Usta uchun xulosa</b>\n\n🚛 {truck}, {year}\n⚠️ {problem}",
        "en": "📝 <b>Summary for the mechanic</b>\n\n🚛 {truck}, {year}\n⚠️ {problem}"},
    "ai_lbl_since": {"ru": "Появилась", "uz": "Paydo bo‘lgan", "en": "Started"},
    "ai_lbl_extra": {"ru": "Доп. признаки", "uz": "Qo‘shimcha belgilar", "en": "Extra signs"},
}


def t(lang: str | None, key: str, **kw) -> str:
    entry = T.get(key)
    if entry is None:
        return key
    text = entry.get(lang or DEFAULT_LANG) or entry.get(DEFAULT_LANG) or key
    return text.format(**kw) if kw else text


def all_variants(key: str) -> set[str]:
    return set(T.get(key, {}).values())
