import re
from typing import Optional
from datetime import datetime, timedelta


class EntityExtractor:
    """Extract entities like phone, name, date, time from conversation text."""

    PHONE_PATTERNS = [
        r'\b(\+?1?\s*[-.]?\s*\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4})\b',
        r'\b(\d{10})\b',
        r'\b(\d{3}[\s.-]\d{3}[\s.-]\d{4})\b',
    ]

    TIME_PATTERNS = [
        r'\b(1[0-2]|0?[1-9]):[0-5][0-9]\s*(?:AM|PM|am|pm)\b',
        r'\b(1[0-2]|0?[1-9])\s*(?:AM|PM|am|pm)\b',
        r'\b([01]?[0-9]|2[0-3]):[0-5][0-9]\b',
    ]

    DATE_KEYWORDS = {
        "today": 0,
        "tomorrow": 1,
        "day after tomorrow": 2,
        "next monday": None,
        "next tuesday": None,
        "next wednesday": None,
        "next thursday": None,
        "next friday": None,
        "next saturday": None,
        "next sunday": None,
    }

    @classmethod
    def extract_phone(cls, text: str) -> Optional[str]:
        for pattern in cls.PHONE_PATTERNS:
            match = re.search(pattern, text)
            if match:
                raw = re.sub(r'[\s\-\.\(\)]', '', match.group(0))
                if len(raw) >= 10:
                    return raw[-10:]
        return None

    @classmethod
    def extract_name(cls, text: str) -> Optional[str]:
        patterns = [
            r'(?:my name is|i am|i\'m|call me|this is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            r'(?:name[:\s]+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    @classmethod
    def extract_date(cls, text: str) -> Optional[str]:
        text_lower = text.lower()
        today = datetime.now()

        for keyword, offset in cls.DATE_KEYWORDS.items():
            if keyword in text_lower:
                if offset is not None:
                    target = today + timedelta(days=offset)
                    return target.strftime("%Y-%m-%d")
                else:
                    day_name = keyword.replace("next ", "")
                    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
                    if day_name in days:
                        target_weekday = days.index(day_name)
                        current_weekday = today.weekday()
                        delta = (target_weekday - current_weekday + 7) % 7
                        if delta == 0:
                            delta = 7
                        target = today + timedelta(days=delta)
                        return target.strftime("%Y-%m-%d")

        date_patterns = [
            r'\b(\d{4}-\d{2}-\d{2})\b',
            r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{4})\b',
            r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s*(\d{4})?\b',
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    if "-" in match.group(0) and len(match.group(0)) == 10:
                        return match.group(0)
                    parts = re.split(r'[/-]', match.group(0))
                    if len(parts) == 3:
                        if len(parts[2]) == 4:
                            month, day, year = parts
                            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                except Exception:
                    pass

        return None

    @classmethod
    def extract_time(cls, text: str) -> Optional[str]:
        for pattern in cls.TIME_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                raw = match.group(0).strip().upper()
                try:
                    if "AM" in raw or "PM" in raw:
                        if ":" in raw:
                            t = datetime.strptime(raw, "%I:%M %p") if " " in raw else datetime.strptime(raw, "%I:%M%p")
                        else:
                            raw_clean = raw.replace("AM", " AM").replace("PM", " PM").strip()
                            t = datetime.strptime(raw_clean, "%I %p")
                        return t.strftime("%H:%M")
                    else:
                        parts = raw.split(":")
                        return f"{int(parts[0]):02d}:{parts[1]}"
                except Exception:
                    pass
        return None

    @classmethod
    def extract_intent(cls, text: str) -> str:
        text_lower = text.lower()
        if any(w in text_lower for w in ["book", "schedule", "appointment", "reserve"]):
            return "book_appointment"
        if any(w in text_lower for w in ["cancel", "remove", "delete"]):
            return "cancel_appointment"
        if any(w in text_lower for w in ["change", "modify", "reschedule", "update"]):
            return "modify_appointment"
        if any(w in text_lower for w in ["show", "see", "list", "view", "what are my", "my appointments"]):
            return "retrieve_appointments"
        if any(w in text_lower for w in ["available", "slots", "openings", "free"]):
            return "fetch_slots"
        if any(w in text_lower for w in ["bye", "goodbye", "end", "hang up", "done", "thank you"]):
            return "end_conversation"
        return "general"

    @classmethod
    def extract_all(cls, text: str) -> dict:
        return {
            "phone": cls.extract_phone(text),
            "name": cls.extract_name(text),
            "date": cls.extract_date(text),
            "time": cls.extract_time(text),
            "intent": cls.extract_intent(text),
        }
