from datetime import datetime
from src.schemas.appointplan import BXAppointment


def get_comment(specialist: dict, patient: dict, code: str, apps: list[dict | BXAppointment]) -> str:
    """Выдает коммент на основе задач"""
    spec = specialist.get('LAST_NAME', '') + ' ' + specialist.get('NAME', '')[0]
    client = patient.get('LAST_NAME', '') + ' ' + patient.get('NAME', '')[0]
    template = f"[*] {spec} - {client}, {code}, " + "{0}, {1} минут."

    def iterator():
        for app in apps:
            if isinstance(app, dict):
                date = datetime.fromisoformat(app.get('ufCrm3StartDate', ''))
                duration = datetime.fromisoformat(app.get('ufCrm3EndDate', '')) - date
            elif isinstance(app, BXAppointment):
                date = app.start
                duration = app.end - app.start              #type:ignore
            date = date.strftime(r'%d.%m.%Y %H:%M')         #type:ignore
            duration = int(duration.total_seconds() // 60)  #type:ignore
            yield template.format(date, duration)
    
    return f'Добавлены занятия:\n[list=1]{'\n'.join(iterator())}[/list]'
