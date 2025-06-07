class appointment:
    entityTypeId = 1036

    class uf:
        specialist = 'assignedById'
        patient = "ufCrm3Children"
        old_patient = "ufCrm3HistoryClient"
        start = "ufCrm3StartDate"
        end = "ufCrm3EndDate"
        status = "ufCrm3Status"
        code = "ufCrm3Code"
    
    class lfv:          # Обновится при запуске приложения
        idByCode = {}   # {"L": "52"}
        codeById = {}   # {"52": "L"}


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
        "28": "A", "26": "ABA", "40": "d", "24": "D 3,5+", "42": "d-ава", "23": "D1-3,5",
        "44": "dd", "45": "dL", "43": "dNP", "46": "dP", "38": "i", "21": "L",
        "22": "LM", "32": "NP", "30": "NТ", "33": "P", "25": "R", "27": "Z",
        "37": "АВА-Р", "39": "К", "36": "КИТ", "41": "КК", "31": "НДГ", "35": "СИ"
    }
