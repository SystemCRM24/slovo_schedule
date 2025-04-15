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
     @returns object - объект рсаписания на указанный промежуток врмеени
     */
    async getSchedule(fromDate, toDate) {
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
     * @returns {Promise<[{specCodes: string[], name: string}>}
     */
    async getSpecialists() {
        // mock for a while
        return {
            'Борзенкова Т.Н.': ['PP'],
            'Федькович С.А.': ['ABA-терапия'],
            'Гарькуша И.А.': ['L', 'D', 'LR'],
            'Дорошева Т.П.': ['Нейропсихолог'],
            'Мамедова Т.И.': ['L', 'D'],
            'Вагизов С.С.': ['НДГ'],
            'Шлык В.С': ['НДГ'],
            'Мазницкая А.Д': [],
            'Швец А.А.': ['Сенсор'],
            'Липина А.В.': ['ABA-терапия'],
            'Позова О.В.': ['Психолог']
        };
    }

}

const api = new APIClient();
export default api;
