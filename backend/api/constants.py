class constants:

    class entityTypeId:
        appointment = 1036
        workSchedule = 1042

    departments = {
        "28": "A", "26": "ABA", "40": "d", "24": "D 3,5+", "42": "d-ава", "23": "D1-3,5",
        "44": "dd", "45": "dL", "43": "dNP", "46": "dP", "38": "i", "21": "L",
        "22": "LM", "32": "NP", "30": "NТ", "33": "P", "25": "R", "27": "Z",
        "37": "АВА-Р", "39": "К", "36": "КИТ", "41": "КК", "31": "НДГ", "35": "СИ"
    }

    class uf:
        class appointment:
            patient = "ufCrm3Children"
            old_patient = "ufCrm3HistoryClient"
            start = "ufCrm3StartDate"
            end = "ufCrm3EndDate"
            status = "ufCrm3Status"
            code = "ufCrm3Code"

        class workSchedule:
            date = "ufCrm4Date"
            intervals = "ufCrm4Intervals"
    
    class listFieldValues:
        class appointment:
            statusById = {50: 'booked', 51: 'confirmed'}
            idByStatus = {'booked': 50, 'confirmed': 51}
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