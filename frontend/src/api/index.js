import {getDateRange, getDateWithTime} from "../utils/dates.js";
import BX24Wrapper from "./bx24Wrapper.js";


export const constants = {
    entityTypeId: {appointment: 1036, workSchedule: 1042},
    departments: {
        "28": "A", "26": "ABA", "40": "d", "24": "D 3,5+", "42": "d-ава", "23": "D1-3,5",
        "44": "dd", "45": "dL", "43": "dNP", "46": "dP", "38": "i", "21": "L",
        "22": "LM", "32": "NP", "30": "NТ", "33": "P", "25": "R", "27": "Z",
        "37": "АВА-Р", "39": "К", "36": "КИТ", "41": "КК", "31": "НДГ", "35": "СИ"
    },
    uf: {
        appointment: {
            patient: "ufCrm3Children",
            start: "ufCrm3StartDate",
            end: "ufCrm3EndDate",
            status: "ufCrm3Status",
            code: "ufCrm3Code"
        },
        workSchedule: {
            date: "ufCrm4Date",
            intervals: "ufCrm4Intervals"
        }
    },
    listFieldValues: {
        appointment: {
            statusById: {50: 'booked', 51: 'confirmed'},
            idByStatus: {'booked': 50, 'confirmed': 51},
            idByCode: {
                "L": "52", "A": "53", "LM": "54", "R": "55", "D": "56", "СИ": "57",
                "НДГ": "58", "АБА": "59", "NP ИПР": "60", "NP  IQ": "61", "P": "62", "Z": "63",
                "КИТ": "64", "d": "65", "d-L": "66", "d-P": "67", "d-Z": "68", "d-НЭК": "69", "d-NP": "70",
                "d-Р": "71", "d-ABA": "72", "d-СИ": "73", "АВА-ИА": "74", "АВА-Р": "75"
            },
            codeById: {
                "52": "L", "53": "A", "54": "LM", "55": "R", "56": "D", "57": "СИ",
                "58": "НДГ", "59": "АБА", "60": "NP ИПР", "61": "NP IQ", "62": "P", "63": "Z",
                "64": "КИТ", "65": "d", "66": "d-L", "67": "d-P", "68": "d-Z", "69": "d-НЭК",
                "70": "d-NP", "71": "d-Р", "72": "d-ABA", "73": "d-СИ", "74": "АВА-ИА", "75": "АВА-Р"
            }
        }
    }
}


class APIClient {

    constructor() {
        // this.bx = new BX24Wrapper();
        this.serverUrl = 'https://3638421-ng03032.twc1.net/slovo_schedule_api/front';
        this.testFrom = new Date('2025-04-27T21:00:00.000Z');
        this.testTo = new Date('2025-04-30T20:59:59.167Z');
    }

    async ping() {
        console.log('pong');
    }

    /**
     * Получает Специалистов и возвращает Объект по следующему соглашению
     * @returns {Promise<Object.<string, { name: string, departments: number[] }>>}
     */
    async getSpecialists() {
        const response = await fetch(`${this.serverUrl}/get_specialist`);
        return await response.json();
    }

    /**
     * Получение детей.
     * @returns {Promise<Object.<string, string>>}
     */
    async getClients() {
        const response = await fetch(`${this.serverUrl}/get_clients`);
        return await response.json();
    }

    /**
     @param {Date} from - начало промежутка дат
     @param {Date} to - конец промежутка дат
      * Структура возвращаемого объекта:
      * {
      *   [id: string]: {            // Идентификатор специалиста
      *     [date: Date]: Array<{    // День и массив с записями на прием
      *       id: number,            // id смарт-процесса Расписания
      *       start: Date,
      *       end: Date,
      *       patient: {
      *           id: string,
      *           type: string
      *       },
      *       status: string
      *     }>
      *   }
      * }
     @returns object - объект рсаписания на указанный промежуток врмеени
     */
    async getSchedules(from, to) {
        const response = await fetch(`${this.serverUrl}/get_schedules?start=${from.toISOString()}&end=${to.toISOString()}`);
        const data = await response.json();
        for ( const [specId, dateData] of Object.entries(data) ) {
            const correctData = {};
            for ( const [day, appointments] of Object.entries(dateData)) {
                correctData[new Date(day)] = appointments;
                for ( const appointment of appointments ) {
                    appointment.start = new Date(appointment.start);
                    appointment.end = new Date(appointment.end);
                }
            }
            data[specId] = correctData;
        }
        console.log(data);
        return data;
    }

    /**
     * Получение рабочего графика всех специалистов.
     * @param {Date} from Объект Date - начало периода для фильтрации
     * @param {Date} to Объект Date - окончание периода для фильтрации
     * Структура возвращаемого объекта:
     * {
     *   [id: string]: {            // Идентификатор специалиста
     *     [date: Date]: {          //
     *        id: string,           // id смарт-процесса Рабочего графика
     *        intervals: Array<{
     *          start: Date,
     *          end: Date
     *        }>
     *     }
     *   }
     * }
     */
    async getWorkSchedules(from, to) {
        const response = await fetch(`${this.serverUrl}/get_work_schedules?start=${from.toISOString()}&end=${to.toISOString()}`);
        const data = await response.json();
        for ( const [specId, dateData] of Object.entries(data) ) {
            const currentData = {};
            for ( const [day, intervalsData] of Object.entries(dateData) ) {
                currentData[new Date(day)] = {
                    id: String(intervalsData.id),
                    intervals: intervalsData.intervals.map(i => {
                    return {start: new Date(i.start), end: new Date(i.end)}
                })
                }
            }
            data[String(specId)] = currentData;
        }
        return data;
    }

    async getDeals(filter = {}) {
        const deals = await this.bx.callListMethod('crm.deal.list', {'FILTER': filter});
        console.log(deals);
        return deals;
    }

    async _createCrmItem(entityTypeId, fields) {
        return await this.bx.callMethod('crm.item.add', {entityTypeId, fields});
    }

    async _getCrmItem(entityTypeId, id) {
        return await this.bx.callMethod('crm.item.get', {entityTypeId, id, useOriginalUfNames: 'N'});
    }

    async _updateCrmItem(entityTypeId, id, fields) {
        return await this.bx.callMethod('crm.item.update', {entityTypeId, id, fields});
    }

    async _deleteCrmItem(entityTypeId, id) {
        return await this.bx.callMethod('crm.item.delete', {entityTypeId, id});
    }

    /**
     * Создает элемент смарт-процесса - расписание
     * @param {object} data - Объект расписания
     * @param {string} data.specialist - ИД специалиста
     * @param {string} data.patient - ИД пациента - ребенка
     * @param {Date} data.start - Начало приема
     * @param {Date} data.end - Конец приема
     * @param {string} data.status - Статус
     * @param {string} data.code - код занятия
     */
    async createAppointment(data) {
        const fields = {
            ASSIGNED_BY_ID: data.specialist,
            [constants.uf.appointment.patient]: data.patient,
            [constants.uf.appointment.start]: data.start,
            [constants.uf.appointment.end]: data.end,
            [constants.uf.appointment.status]: constants.listFieldValues.appointment.idByStatus[data.status],
            [constants.uf.appointment.code]: constants.listFieldValues.appointment.idByCode[data.code]
        };
        const response = await this._createCrmItem(constants.entityTypeId.appointment, fields);
        return response.item;
    }

    /**
     * Получение информации о элементе смарт-процесса - расписания
     * @param {string} id
     */
    async getAppointment(id) {
        return await this._getCrmItem(constants.entityTypeId.appointment, id);
    }

    /**
     * Обновляет элемент смарт-процесса - расписание
     * @param {string} id - ИД Расписания для обновления
     * @param {object} data - Объект расписания
     * @param {string} data.specialist - ИД специалиста
     * @param {string} data.patient - ИД пациента - ребенка
     * @param {Date} data.start - Начало приема
     * @param {Date} data.end - Конец приема
     * @param {string} data.status - Статус
     * @param {string} data.code - код занятия
     */
    async updateAppointment(id, data) {
        const fields = {
            ASSIGNED_BY_ID: data.specialist,
            [constants.uf.appointment.patient]: data.patient,
            [constants.uf.appointment.start]: data.start,
            [constants.uf.appointment.end]: data.end,
            [constants.uf.appointment.status]: constants.listFieldValues.appointment.idByStatus[data.status],
            [constants.uf.appointment.code]: constants.listFieldValues.appointment.idByCode[data.code]
        };
        const response = await this._updateCrmItem(constants.entityTypeId.appointment, id, fields);
        return response.item;
    }

    /**
     * Удаляет запись о приеме
     * @param {string} id - ид записи (Расписания)
     * @returns
     */
    async deleteAppointment(id) {
        return await this._deleteCrmItem(constants.entityTypeId.appointment, id);
    }

    /**
     * Создает элемент смарт-процесса - график
     * @param {object} data - Объект графика
     * @param {string} data.specialist - ИД специалиста
     * @param {string} data.date - дата, для которой нужно создать расписание
     * @param {Array<{start: Date, end: Date}>} data.intervals - Интервалы, которые обозначают рабочее время
     */
    async createWorkSchedule(data) {
        const intervals = data.intervals.map(i => `${i.start.getTime()}:${i.end.getTime()}`);
        const fields = {
            ASSIGNED_BY_ID: data.specialist,
            [constants.uf.workSchedule.date]: data.date,
            [constants.uf.workSchedule.intervals]: intervals
        }
        const response = await this._createCrmItem(constants.entityTypeId.workSchedule, fields);
        return response.item;
    }

    /**
     * Получает элемент смарт-процесса - график
     * @param {string} id - ид графика
     */
    async getWorkSchedule(id) {
        return await this._getCrmItem(constants.entityTypeId.workSchedule, id);
    }

    /**
     * Обновляет элемент смарт-процесса-график
     * @param {string} id - ид графика
     * @param {object} data - Объект графика
     * @param {string} data.specialist - ИД специалиста
     * @param {string} data.date - дата, для которой нужно создать расписание
     * @param {Array<{start: Date, end: Date}>} data.intervals - Интервалы, которые обозначают рабочее время
     */
    async updateWorkSchedule(id, data) {
        const intervals = data.intervals.map(i => `${i.start.getTime()}:${i.end.getTime()}`);
        const fields = {
            ASSIGNED_BY_ID: data.specialist,
            [constants.uf.workSchedule.date]: data.date,
            [constants.uf.workSchedule.intervals]: intervals
        }
        const response = await this._updateCrmItem(constants.entityTypeId.workSchedule, id, fields);
        return response.item;
    }

    /**
     * Удаляет запись о рабочем графике
     * @param {string} id - ид рабочего графика
     * @returns
     */
    async deleteWorkSchedule(id) {
        return await this._deleteCrmItem(constants.entityTypeId.workSchedule, id);
    }
}


const apiClient = new APIClient();

export default apiClient;
