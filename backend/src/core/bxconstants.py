class appointment:
    entityTypeId = 1036

    class uf:
        specialist = 'assignedById'
        patient = "ufCrm3Children"
        start = "ufCrm3StartDate"
        end = "ufCrm3EndDate"
        code = "ufCrm3Code"
        status = "ufCrm3Status"
        deal_id = "ufCrm3Dealid"
        abonnement = "ufCrm3_1755268035495"   # ПО факту, дата отмены абонемента.

    class lfv:          # Обновится при запуске приложения
        idByCode = {}   # {"L": "52"}
        codeById = {}   # {"52": "L"}
        idByStatus = {}
        statusById = {}


class schedule:
    entityTypeId = 1042

    class uf:
        specialist = 'assignedById'
        date = "ufCrm4Date"
        intervals = "ufCrm4Intervals"


class deal:
    pass


class BXConstants:
    appointment = appointment
    schedule = schedule
    deal = deal

    departments = {
        "71": "А", "59": "АБА", "60": "АБА-К", "82": "АВС", "84": "Б-трэйн", "78": "БАК", "77": "БОС", "67": "Д1",
        "68": "Д2", "53": "дАБА", "55": "дЗ", "56": "дИПР", "52": "дКНП", "90": "дКПс", "50": "дЛ", "51": "дНП",
        "57": "дПС", "54": "дСИ", "85": "ДЭНАС", "69": "З", "70": "З-в", "89": "З-гр", "62": "ИПР", "61": "КФ", "64": "Л",
        "65": "Л-В", "66": "ЛМ", "76": "ЛР", "86": "Н-порт", "72": "НДГ", "87": "НЭК", "63": "ПРР", "74": "ПС-в",
        "73": "ПС-д", "75": "Р", "88": "РТ", "58": "СИ", "80": "СС", "79": "ТТ", "81": "Форб", "91": "ПШ", "92": "КЛ",
        "93": "ДРЗ", "94": "СК"
    }
    department_ids = {v: k for k, v in departments.items()}
