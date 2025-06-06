class appointment:
    entityTypeId = 1036

    class uf:
        specialist: 'assignedById'
        patient = "ufCrm3Children"
        old_patient = "ufCrm3HistoryClient"
        start = "ufCrm3StartDate"
        end = "ufCrm3EndDate"
        status = "ufCrm3Status"
        code = "ufCrm3Code"
    
    class lfv:
        idByCode = {
            "L": "52", "A": "53", "LM": "54", "R": "55", "D": "56", "СИ": "57",
            "НДГ": "58", "АБА": "59", "NP ИПР": "60", "NP  IQ": "61", "P": "62", "Z": "63",
            "КИТ": "64", "d": "65", "d-L": "66", "d-P": "67", "d-Z": "68", "d-НЭК": "69", "d-NP": "70",
            "d-Р": "71", "d-ABA": "72", "d-СИ": "73", "АВА-ИА": "74", "АВА-Р": "75"
        }
        codeById = {
            "52": "L", "53": "A", "54": "LM", "55": "R", "56": "D", "57": "СИ",
            "58": "НДГ", "59": "АБА", "60": "NP ИПР", "61": "NP IQ", "62": "P", "63": "Z",
            "64": "КИТ", "65": "d", "66": "d-L", "67": "d-P", "68": "d-Z", "69": "d-НЭК",
            "70": "d-NP", "71": "d-Р", "72": "d-ABA", "73": "d-СИ", "74": "АВА-ИА", "75": "АВА-Р"
        }


class schedule:
    entityTypeId = 1042

    class uf:
        date = "ufCrm4Date"
        intervals = "ufCrm4Intervals"


class deal:
    pass


class BXConstants:
    appointment = appointment
    schedule = schedule
    deal = deal
