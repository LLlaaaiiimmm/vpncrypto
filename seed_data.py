"""Seed the database with realistic demo feedback data."""
import sqlite3
import os
import random
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "budtender.db")

DEMO_FEEDBACKS = [
    {
        "category": "complaint",
        "message": "The air conditioning in our store has been broken for 2 weeks. It's extremely hot inside and customers are complaining. We've reported this multiple times but no one comes to fix it.",
        "translation_en": "The air conditioning in our store has been broken for 2 weeks. It's extremely hot inside and customers are complaining. We've reported this multiple times but no one comes to fix it.",
        "translation_ru": "Кондиционер в нашем магазине сломан уже 2 недели. Внутри очень жарко и клиенты жалуются. Мы сообщали об этом несколько раз, но никто не приходит чинить.",
        "summary": "Broken AC for 2 weeks, multiple reports ignored, customers complaining about heat.",
        "tags": "Equipment,Store",
        "detected_language": "en"
    },
    {
        "category": "idea",
        "message": "เราควรมีระบบส่วนลดสำหรับลูกค้าที่กลับมาซื้อซ้ำ จะช่วยเพิ่มยอดขายได้มากเลย",
        "translation_en": "We should have a discount system for returning customers. It would greatly help increase sales.",
        "translation_ru": "Нам нужна система скидок для постоянных клиентов. Это значительно увеличит продажи.",
        "summary": "Proposes loyalty discount system for returning customers to boost sales.",
        "tags": "Product,Customer",
        "detected_language": "th"
    },
    {
        "category": "complaint",
        "message": "My manager constantly changes the schedule without notifying us. Last week I showed up for my shift and was told I wasn't working that day. This has happened 3 times this month.",
        "translation_en": "My manager constantly changes the schedule without notifying us. Last week I showed up for my shift and was told I wasn't working that day. This has happened 3 times this month.",
        "translation_ru": "Мой менеджер постоянно меняет расписание, не уведомляя нас. На прошлой неделе я пришёл на смену, и мне сказали, что я не работаю. Это уже случилось 3 раза за месяц.",
        "summary": "Manager changes schedule without notice, causing shift confusion 3 times this month.",
        "tags": "Schedule,Management",
        "detected_language": "en"
    },
    {
        "category": "recommendation",
        "message": "I think we need better training for new budtenders. Many new hires don't know enough about the products and can't answer customer questions properly. A 2-day training program would help a lot.",
        "translation_en": "I think we need better training for new budtenders. Many new hires don't know enough about the products and can't answer customer questions properly. A 2-day training program would help a lot.",
        "translation_ru": "Я думаю, нам нужно лучшее обучение для новых продавцов. Многие новички недостаточно знают о продуктах и не могут нормально ответить на вопросы покупателей. Двухдневная программа обучения очень бы помогла.",
        "summary": "Recommends better training program for new hires who lack product knowledge.",
        "tags": "Training,Product",
        "detected_language": "en"
    },
    {
        "category": "complaint",
        "message": "เงินเดือนเดือนที่แล้วเข้าช้าไป 5 วัน ไม่มีใครแจ้งล่วงหน้าเลย ทำให้มีปัญหาเรื่องค่าเช่าบ้าน",
        "translation_en": "Last month's salary was 5 days late with no prior notice. This caused problems with my rent payment.",
        "translation_ru": "Зарплата за прошлый месяц задержалась на 5 дней без предупреждения. Из-за этого возникли проблемы с оплатой аренды.",
        "summary": "Salary delayed 5 days without warning, causing rent payment issues.",
        "tags": "Salary,Communication",
        "detected_language": "th"
    },
    {
        "category": "idea",
        "message": "We should have a staff chat group where we can share tips about products and customer handling. Right now every store works in isolation and we don't learn from each other.",
        "translation_en": "We should have a staff chat group where we can share tips about products and customer handling. Right now every store works in isolation and we don't learn from each other.",
        "translation_ru": "Нам нужен групповой чат для персонала, где можно делиться советами о продуктах и работе с клиентами. Сейчас каждый магазин работает изолированно, и мы не учимся друг у друга.",
        "summary": "Suggests staff communication channel for sharing product tips across stores.",
        "tags": "Communication,Training",
        "detected_language": "en"
    },
    {
        "category": "complaint",
        "message": "There's a conflict between two team members that has been going on for weeks. It's affecting the whole team atmosphere. Management knows about it but hasn't done anything.",
        "translation_en": "There's a conflict between two team members that has been going on for weeks. It's affecting the whole team atmosphere. Management knows about it but hasn't done anything.",
        "translation_ru": "Конфликт между двумя членами команды продолжается уже несколько недель. Это влияет на атмосферу всей команды. Руководство знает об этом, но ничего не делает.",
        "summary": "Ongoing team conflict for weeks, management aware but not acting, affecting morale.",
        "tags": "Conflict,Management",
        "detected_language": "en"
    },
    {
        "category": "recommendation",
        "message": "ควรมีกล้องวงจรปิดที่ทำงานได้ดีกว่านี้ กล้อง 2 ตัวในร้านพังไปหลายเดือนแล้ว ไม่ปลอดภัยเลย",
        "translation_en": "We should have better working CCTV cameras. 2 cameras in the store have been broken for months. It's not safe.",
        "translation_ru": "Камеры видеонаблюдения должны работать лучше. 2 камеры в магазине сломаны уже несколько месяцев. Это небезопасно.",
        "summary": "Broken CCTV cameras for months creating safety concerns in store.",
        "tags": "Safety,Equipment",
        "detected_language": "th"
    },
    {
        "category": "other",
        "message": "Just wanted to say that the new product display layout is really great! Customers love it and it's much easier to explain products now. Good job to whoever designed it!",
        "translation_en": "Just wanted to say that the new product display layout is really great! Customers love it and it's much easier to explain products now. Good job to whoever designed it!",
        "translation_ru": "Просто хотел сказать, что новая раскладка витрины отличная! Клиентам нравится, и теперь намного проще объяснять про продукты. Отличная работа!",
        "summary": "Positive feedback about new product display layout, customers and staff like it.",
        "tags": "Product,Store",
        "detected_language": "en"
    },
    {
        "category": "complaint",
        "message": "The cleaning supplies are always running out and we have to buy our own. This is not fair. We need regular stock of cleaning products for the store hygiene.",
        "translation_en": "The cleaning supplies are always running out and we have to buy our own. This is not fair. We need regular stock of cleaning products for the store hygiene.",
        "translation_ru": "Чистящие средства постоянно заканчиваются, и нам приходится покупать свои. Это несправедливо. Нужны регулярные поставки средств для гигиены магазина.",
        "summary": "Cleaning supplies constantly running out, staff forced to buy their own.",
        "tags": "Hygiene,Store",
        "detected_language": "en"
    },
    {
        "category": "idea",
        "message": "ถ้ามีแท็บเล็ตที่เคาน์เตอร์ให้ลูกค้าดูข้อมูลสินค้าเองได้ จะช่วยลดภาระงานของพนักงานได้มาก โดยเฉพาะช่วงที่ลูกค้าเยอะ",
        "translation_en": "If we had tablets at the counter for customers to browse product information, it would greatly reduce staff workload, especially during busy times.",
        "translation_ru": "Если бы на прилавке были планшеты для просмотра информации о продуктах, это значительно снизило бы нагрузку на персонал, особенно в часы пик.",
        "summary": "Proposes tablets at counter for customer self-service to reduce staff workload.",
        "tags": "Equipment,Customer",
        "detected_language": "th"
    },
    {
        "category": "complaint",
        "message": "I feel like the overtime policy is unclear. Sometimes we work extra hours but it's not properly tracked or compensated. Need clear guidelines on this.",
        "translation_en": "I feel like the overtime policy is unclear. Sometimes we work extra hours but it's not properly tracked or compensated. Need clear guidelines on this.",
        "translation_ru": "Политика сверхурочных непонятна. Иногда мы работаем дополнительные часы, но это не отслеживается и не компенсируется. Нужны чёткие правила.",
        "summary": "Overtime policy unclear, extra hours not tracked or compensated properly.",
        "tags": "Salary,Policy",
        "detected_language": "en"
    },
]


def seed():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    db = sqlite3.connect(DB_PATH)

    existing = db.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]
    if existing > 0:
        print(f"Database already has {existing} feedback entries. Skipping seed.")
        db.close()
        return

    now = datetime.utcnow()
    statuses = ["new", "new", "new", "read", "read", "in_progress", "resolved"]

    for i, fb in enumerate(DEMO_FEEDBACKS):
        created = now - timedelta(days=random.randint(0, 29), hours=random.randint(0, 23), minutes=random.randint(0, 59))
        sub_id = f"WDN-{random.randint(100,999)}-{random.randint(10,99)}"
        status = random.choice(statuses)
        ip_hash = f"demo_hash_{i}"

        note = ""
        if status == "resolved":
            note = "Issue addressed with store manager."
        elif status == "in_progress":
            note = "Looking into this."

        db.execute("""
            INSERT INTO feedback (submission_id, category, message, status, ip_hash, user_agent,
                ai_status, translation_en, translation_ru, summary, tags, detected_language,
                private_note, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 'done', ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            sub_id, fb["category"], fb["message"], status, ip_hash, "Mozilla/5.0 Demo",
            fb["translation_en"], fb["translation_ru"], fb["summary"], fb["tags"],
            fb["detected_language"], note,
            created.isoformat(), created.isoformat()
        ))

    db.commit()
    print(f"Seeded {len(DEMO_FEEDBACKS)} demo feedback entries.")
    db.close()


if __name__ == "__main__":
    seed()
