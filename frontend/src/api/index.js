import {getDateRange} from "../utils/dates.js";
import BX24Wrapper from "./bx24Wrapper.js";


class APIClient {
    constructor() {
        this.bx = new BX24Wrapper();
    }

    /**
     * This method is mocked for a while
     @async
     @param {Date} fromDate - начало промежутка дат
     @param {Date} toDate - конец промежутка дат
     @returns {Promise<Object<string|number, Object<Date, Array<{
      start: Date, end: Date, patient: {name: string, type: string}, status: "booked" | "confirmed" | "free" | "na"
      }>>>>}
     объект расписания занятий по сотрудникам
     */
    async getSchedule(fromDate, toDate) {
        /**
         * Структура объекта:
         * {
         *     "<id пользователя>: {
         *         <строка даты в iso-формате для описания дня>: [
         *             {
         *                 start: <строка даты в iso-формате>,
         *                 end: <строка даты в iso-формате>,
         *                 patient: {
         *                     name: "Егорова Я.""
         *                     type: "L"
         *                 },
         *                 status: "booked",
         *             },
         *         ]
         *     }
         * }
         */
            // MUST BE DELETED LATER
        const tmpVisitationStartDate1 = new Date(fromDate);
        const tmpVisitationStartDate2 = new Date(fromDate);
        const tmpVisitationEndDate1 = new Date(fromDate);
        const tmpVisitationEndDate2 = new Date(fromDate);
        tmpVisitationStartDate1.setHours(9);
        tmpVisitationEndDate1.setHours(9, 30);
        tmpVisitationStartDate2.setHours(18, 30);
        tmpVisitationEndDate2.setHours(19)
        return {
            "8":
                {
                    [fromDate]: [
                        {
                            start: tmpVisitationStartDate1,
                            end: tmpVisitationEndDate1,
                            patient: {
                                name: "Тестовый П.",
                                type: "ABA",
                            },
                            status: "booked"  // booked / confirmed / free / na,
                        },
                        {
                            start: tmpVisitationStartDate2,
                            end: tmpVisitationEndDate2,
                            patient: {
                                name: "Тестовый2 П.",
                                type: "ABA",
                            },
                            status: 'confirmed',
                        }
                    ],
                },
        };
    }


    /**
     * This method is mocked for a while
     @async
     @param {Date} fromDate - начало промежутка дат
     @param {Date} toDate - конец промежутка дат
     @returns {Promise<Object<string|number, Object<Date, Array<{start: Date, end: Date}>>>>}
     объект на указаный промежуток времени, где описан рабочий график сотрудников.
     */
    async getWorkSchedule(fromDate, toDate) {
        /**
         * Структура объекта:
         * {
         *     "<id пользователя >": {
         *         <строка даты в iso-формате для описания дня>: [
         *             {
         *                 start: <строка даты в iso-формате>,
         *                 end: <строка даты в iso-формате>,
         *             },
         *         ]
         *     }
         * }
         */
        if (fromDate < toDate) {
            let schedule = {};
            const specialists = [
                "8", "9",
                "11", "12", "13",
                "15", "16",
                "17", "18", "19",
                "20", "21", "22",
                "23"
            ]
            const dateRange = getDateRange(fromDate, toDate)
            for (const specialist of specialists) {
                schedule[specialist] = {};
                // strange mock for a while, i know, excusez-moi, mon ami :)
                for (const date of dateRange) {
                    if (date.getTime() !== toDate.getTime()) {
                        const start1 = new Date(date);
                        const start2 = new Date(date);
                        const end1 = new Date(date);
                        const end2 = new Date(date);
                        start1.setHours(9, 0);
                        start2.setHours(12, 30);
                        end1.setHours(11, 30);
                        end2.setHours(19, 0);
                        schedule[specialist][date] = [
                            {
                                start: start1,
                                end: end1
                            },
                            {
                                start: start2,
                                end: end2
                            }
                        ];
                    } else {
                        schedule[specialist][date] = [];
                    }
                }
            }
            return schedule;
        }
    }

    /**
     * This method is mocked for a while
     @async
     @returns {Promise<Object<string|int, {name: string, departments: string[]}>>}
     */
    async getSpecialists() {
        // mock for a while
        return {
            "8": {
                "name": "Ходырева Н.",
                "departments": [
                    "ABA",
                    "d"
                ]
            },
            "9": {
                "name": "Мазницкая А.",
                "departments": [
                    "НДГ",
                    "СИ"
                ]
            },
            "11": {
                "name": "Железнова М.",
                "departments": [
                    "NP"
                ]
            },
            "12": {
                "name": "Исмагилова С.",
                "departments": [
                    "R"
                ]
            },
            "13": {
                "name": "Вагизов С.",
                "departments": [
                    "НДГ"
                ]
            },
            "15": {
                "name": "Александра Ш.",
                "departments": [
                    "НДГ",
                    "СИ"
                ]
            },
            "16": {
                "name": "Слесь И.",
                "departments": [
                    "ABA",
                    "d-ава"
                ]
            },
            "17": {
                "name": "Шлык В.",
                "departments": [
                    "NP",
                    "НДГ"
                ]
            },
            "18": {
                "name": "Статина Е.",
                "departments": [
                    "dNP",
                    "NP",
                    "КИТ"
                ]
            },
            "19": {
                "name": "Федькович С.",
                "departments": [
                    "ABA",
                    "d",
                    "L",
                    "LM"
                ]
            },
            "20": {
                "name": "Гарькуша И.",
                "departments": [
                    "d",
                    "dL",
                    "L",
                    "LM"
                ]
            },
            "21": {
                "name": "Мамедова Т.",
                "departments": [
                    "d",
                    "dL",
                    "L",
                    "LM",
                    "Z"
                ]
            },
            "22": {
                "name": "Дорошева Т.",
                "departments": [
                    "dL",
                    "dNP",
                    "L",
                    "LM",
                    "NP"
                ]
            },
            "23": {
                "name": "Липина А.",
                "departments": [
                    "ABA"
                ]
            }
        }
    }
}

const apiClient = new APIClient();
export default apiClient;
