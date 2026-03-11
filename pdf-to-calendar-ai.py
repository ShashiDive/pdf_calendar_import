
import sys
import fitz
import os
import json
import base64
import subprocess
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def pdf_to_image(pdf_path):

    with fitz.open(pdf_path) as doc:

        page = doc.load_page(0)

        pix = page.get_pixmap(dpi=300)

        image_path = pdf_path.replace(".pdf", ".png")

        pix.save(image_path)

    return image_path

def extract_events_with_gpt_vision(image_path):

        with open(image_path, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode()

        response = client.responses.create(
        model="gpt-4.1",
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": """
        Extract timetable events.

        Return JSON in this format:

        {
        "events":[
            {
            "subject":"Math",
            "date":"2026-03-09",
            "day_of_week":null,
            "start_time":"08:45",
            "end_time":"10:45"
          }
            ]
        }
        """
                    },
                    {
                        "type": "input_image",
                        "image_url": f"data:image/png;base64,{image_base64}"
                    }
                 ]
              }
            ]
        )

        return response.output[0].content[0].text


def normalize_day(day):

    if not day:
        return None

    day = day.strip().lower()

    day_lookup = {
        "monday": "MO", "mon": "MO",
        "tuesday": "TU", "tue": "TU", "tues": "TU",
        "wednesday": "WE", "wed": "WE",
        "thursday": "TH", "thu": "TH", "thur": "TH", "thurs": "TH",
        "friday": "FR", "fri": "FR",
        "saturday": "SA", "sat": "SA",
        "sunday": "SU", "sun": "SU"
    }

    return day_lookup.get(day)


def create_calendar(events_json, pdf_file):

    events_json = events_json.strip()
    events_json = events_json.replace("```json", "").replace("```", "")
    data = json.loads(events_json)
    events = data["events"]

    ics_file = pdf_file.replace(".pdf", ".ics")

    with open(ics_file, "w") as f:

        f.write("BEGIN:VCALENDAR\n")
        f.write("VERSION:2.0\n")

        for e in events:

            start = e["start_time"].replace(":", "") + "00"
            end = e["end_time"].replace(":", "") + "00"

            f.write("BEGIN:VEVENT\n")
            f.write(f"SUMMARY:{e['subject']}\n")

            if e.get("date"):

                date = e["date"].replace("-", "")

                f.write(f"DTSTART:{date}T{start}\n")
                f.write(f"DTEND:{date}T{end}\n")

            elif e.get("day_of_week"):

                day = normalize_day(e["day_of_week"])

                if day is None:
                    continue

                base_date = "20260105"

                f.write(f"DTSTART:{base_date}T{start}\n")
                f.write(f"DTEND:{base_date}T{end}\n")
                f.write(f"RRULE:FREQ=WEEKLY;BYDAY={day}\n")

            else:
                continue

            f.write("END:VEVENT\n")

        f.write("END:VCALENDAR\n")

    subprocess.run(["open", ics_file])


if __name__ == "__main__":

    pdf_file = sys.argv[1]

    image_path = pdf_to_image(pdf_file)

    events_json = extract_events_with_gpt_vision(image_path)

    create_calendar(events_json, pdf_file)