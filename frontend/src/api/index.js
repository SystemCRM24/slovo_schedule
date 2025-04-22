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
     @returns object - Возвращает объект на указаный промежуток времени, где описана занятость сотрудников.
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
         *                 patient: {
         *                     name: "Егорова Я.""
         *                     type: "L"
         *                 }
         *             },
         *         ]
         *     }
         * }
         */
    }


    /**
     * This method is mocked for a while
     @param {Date} fromDate - начало промежутка дат
     @param {Date} toDate - конец промежутка дат
     @returns object - объект рсаписания на указанный промежуток врмеени
     */
    async getSchedule(fromDate, toDate) {
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
                'Борзенкова Т.Н.', 'Федькович С.А.', 'Гарькуша И.А.',
                'Дорошева Т.П.', 'Мамедова Т.И.', 'Вагизов С.С.',
                'Шлык В.С', 'Мазницкая А.Д', 'Швец А.А.', 'Липина А.В.',
                'Позова О.В.'
            ];
            const dateRange = getDateRange(fromDate, toDate)
            for (const specialist of specialists) {
                schedule[specialist] = {};
                // mock for a while
                for (const date of dateRange) {
                    schedule[specialist][date] = {};
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

const api = new APIClient();
export default api;
