import fitz
import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def extract_text(pdf_path):

    doc = fitz.open(pdf_path)

    text = ""

    for page in doc:
        text += page.get_text()

    return text


def extract_events_with_gpt(text):

    prompt = f"""
You are reading a school exam timetable.

Extract ALL exams and return JSON.

Each exam should contain:

- subject
- date
- start_time
- end_time

Return ONLY JSON.

Timetable:

{text}
"""

    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content


def create_calendar(events_json):

    clean_json = events_json.replace("```json", "").replace("```", "").strip()

    events = json.loads(clean_json)

    with open("exams.ics", "w") as f:

        f.write("BEGIN:VCALENDAR\n")
        f.write("VERSION:2.0\n")

        for e in events:

            start = e["date"].replace("-", "") + "T" + e["start_time"].replace(":", "") + "00"
            end = e["date"].replace("-", "") + "T" + e["end_time"].replace(":", "") + "00"

            f.write("BEGIN:VEVENT\n")
            f.write(f"SUMMARY:{e['subject']} Exam\n")
            f.write(f"DTSTART:{start}\n")
            f.write(f"DTEND:{end}\n")
            f.write("END:VEVENT\n")

        f.write("END:VCALENDAR\n")


if __name__ == "__main__":

    pdf_file = "events.pdf"

    text = extract_text(pdf_file)

    events_json = extract_events_with_gpt(text)

    print("\nExtracted Events:\n")

    print(events_json)

    create_calendar(events_json)

    print("\nCalendar file created: exams.ics")