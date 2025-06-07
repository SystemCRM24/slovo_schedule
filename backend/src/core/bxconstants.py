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

# "52": "L", "53": "A", "54": "LM", "55": "R", "56": "D", "57": "СИ",
# "58": "НДГ", "59": "АБА", "60": "NP ИПР", "61": "NP IQ", "62": "P", "63": "Z",
# "64": "КИТ", "65": "d", "66": "d-L", "67": "d-P", "68": "d-Z", "69": "d-НЭК",
# "70": "d-NP", "71": "d-Р", "72": "d-ABA", "73": "d-СИ", "74": "АВА-ИА", "75": "АВА-Р"



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
