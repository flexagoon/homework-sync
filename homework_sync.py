from datetime import datetime

import caldav
import httpx

import config

with httpx.Client() as client:
    client.post("https://nschool.eljur.ru/ajaxauthorize", data=config.ELJUR)

    tasks = client.get(
        "https://nschool.eljur.ru/journal-api-lms-action"
        "?action=lms.get_tasks&study_year=2024%2F2025&status=assigned",
    ).json()["result"]["tasks"]

with caldav.DAVClient(**config.CALDAV) as client:  # type: ignore[arg-type]
    cal = client.calendar(url=config.CAL_URL)
    for task in tasks:
        try:
            cal.todo_by_uid(str(task["id"]))
            continue
        except caldav.error.NotFoundError:  # type: ignore[attr-defined]
            FORMATIVE_TASK_TYPE = 202

            if task["course_id"] in config.COURSE_BLACKLIST:
                continue

            cal.save_todo(
                uid=str(task["id"]),
                summary=task["name"],
                description=f"https://nschool.eljur.ru/journal-course-action/pg.task?task_id={task["id"]}",
                due=datetime.strptime(
                    task["deadline_at"],
                    "%Y-%m-%d %H:%M:%S",
                ).astimezone(),
                priority=(0 if task["type_evaluation"] == FORMATIVE_TASK_TYPE else 1),
            )

            print("Added task:", task["name"])
