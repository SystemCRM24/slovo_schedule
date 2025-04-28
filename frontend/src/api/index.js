import {getDateRange} from "../utils/dates.js";
import BX24Wrapper from "./bx24Wrapper.js";


class APIClient {
    constructor() {
        this.bx = new BX24Wrapper();
    }

    /**
     * This method is mocked for a while
     @param {Date} fromDate - начало промежутка дат
     @param {Date} toDate - конец промежутка дат
     @returns object - объект расписания занятий по сотрудникам
     */
    async getSchedule(fromDate, toDate) {
        /**
         * Структура объекта:
         * {
         *     "Гарькуша И.": {
         *         <строка даты в iso-формате для описания дня>: [
         *             {
         *                 start: <строка даты в iso-формате>,
         *                 end: <строка даты в iso-формате>,
         *                 patient: {
         *                     name: "Егорова Я.""
         *                     type: "L"
         *                 }
         *             },
         *         ]
         *     }
         * }
         */
        return {};
    }


    /**
     * This method is mocked for a while
     @param {Date} fromDate - начало промежутка дат
     @param {Date} toDate - конец промежутка дат
     @returns object - Возвращает объект на указаный промежуток времени, где описан рабочий график сотрудников.
     */
    async getWorkSchedule(fromDate, toDate) {
        /**
         * Структура объекта:
         * {
         *     "Гарькуша И.А.": {
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
                "Ходырева Н.", "Мазницкая А.", "Железнова М.",
                "Исмагилова С.", "Вагизов С.", "Александра Ш.",
                "Слесь И.", "Шлык В.", "Статина Е.",
                "Федькович С.", "Гарькуша И.", "Мамедова Т.",
                "Дорошева Т.", "Липина А."
            ]
            const dateRange = getDateRange(fromDate, toDate)
            for (const specialist of specialists) {
                schedule[specialist] = {};
                // strange mock for a while, i know, excuse moi
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
     * This method is mocked fpr a while
     * @returns {Promise<{string: {}}>}
     */
    async getSpecialists() {
        // mock for a while
        return {
            "Ходырева Н.": {
                "id": "8",
                "departments": [
                    "ABA",
                    "d"
                ]
            },
            "Мазницкая А.": {
                "id": "9",
                "departments": [
                    "НДГ",
                    "СИ"
                ]
            },
            "Железнова М.": {
                "id": "11",
                "departments": [
                    "NP"
                ]
            },
            "Исмагилова С.": {
                "id": "12",
                "departments": [
                    "R"
                ]
            },
            "Вагизов С.": {
                "id": "13",
                "departments": [
                    "НДГ"
                ]
            },
            "Александра Ш.": {
                "id": "15",
                "departments": [
                    "НДГ",
                    "СИ"
                ]
            },
            "Слесь И.": {
                "id": "16",
                "departments": [
                    "ABA",
                    "d-ава"
                ]
            },
            "Шлык В.": {
                "id": "17",
                "departments": [
                    "NP",
                    "НДГ"
                ]
            },
            "Статина Е.": {
                "id": "18",
                "departments": [
                    "dNP",
                    "NP",
                    "КИТ"
                ]
            },
            "Федькович С.": {
                "id": "19",
                "departments": [
                    "ABA",
                    "d",
                    "L",
                    "LM"
                ]
            },
            "Гарькуша И.": {
                "id": "20",
                "departments": [
                    "d",
                    "dL",
                    "L",
                    "LM"
                ]
            },
            "Мамедова Т.": {
                "id": "21",
                "departments": [
                    "d",
                    "dL",
                    "L",
                    "LM",
                    "Z"
                ]
            },
            "Дорошева Т.": {
                "id": "22",
                "departments": [
                    "dL",
                    "dNP",
                    "L",
                    "LM",
                    "NP"
                ]
            },
            "Липина А.": {
                "id": "23",
                "departments": [
                    "ABA"
                ]
            }
        };
    }
}

const apiClient = new APIClient();
export default apiClient;
