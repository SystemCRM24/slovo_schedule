import {getDateRange} from "../utils/dates.js";
import BX24Wrapper from "./bx24Wrapper.js";


const constants = {
    entityTypeId: {appointment: 1036, workSchedule: 1042},
    departments: {
        "28": "A", "26": "ABA", "40": "d", "24": "D 3,5+", "42": "d-ава", "23": "D1-3,5",
        "44": "dd", "45": "dL", "43": "dNP", "46": "dP", "38": "i", "21": "L",
        "22": "LM", "32": "NP", "30": "NТ", "34": "P", "25": "R", "27": "Z",
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
                "d-Р": "71", "d-ABA": "72", "d-СИ": "73", "АВА-ИА": "74","АВА-Р": "75"
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
        this.bx = new BX24Wrapper();
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
        const response = await this.bx.callListMethod(
            'user.get',
            {'@UF_DEPARTMENT': Object.keys(constants.departments)}
        );
        const specialists = {};
        for ( const user of response ) {
            const name = user['LAST_NAME'] + " " + user['NAME'].charAt(0) + ".";
            const userDepratments = user['UF_DEPARTMENT'] || [];
            const departments = userDepratments.map(d => constants.departments[d]);
            specialists[user.ID] = {name, departments};
        }
        return specialists;
    }

    /**
     * Получение детей.
     * @returns {Promise<Object.<string, string>>}
     */
    async getClients() {
        const params = {
            filter: {TYPE_ID: "CLIENT"},
            order: {LAST_NAME: 'ASC', NAME: 'ASC'},
            select: ['ID', 'NAME', 'LAST_NAME']
        };
        const response = await this.bx.callListMethod('crm.contact.list', params);
        const result = {};
        for ( const client of response ) {
            const full_name = client.NAME + (client.LAST_NAME ? ` ${client.LAST_NAME}` : '');
            result[client.ID] = full_name;
        }
        return result;
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
        const params = {
            entityTypeId: constants.entityTypeId.appointment,
            filter: {
                [`>=${constants.uf.appointment.start}`]: from,
                [`<=${constants.uf.appointment.end}`]: to,
            },
            order: {[constants.uf.appointment.start]: 'ASC'}
        }
        const response = await this.bx.callListMethod('crm.item.list', params);
        const schedule = {};
        for ( const itemsObject of response ) {
            for ( const appointment of itemsObject.items ) {
                const specialistId = appointment.assignedById;
                const start = new Date(appointment[constants.uf.appointment.start]);
                const startOfDay = new Date(start);
                // startOfDay.setHours(0, 0, 0, 0);
                const end = new Date(appointment[constants.uf.appointment.end]);
                const patientId = appointment[constants.uf.appointment.patient];
                const patientTypeId = (appointment[constants.uf.appointment.code] || [''])[0];
                const patientType = constants.listFieldValues.appointment.codeById[patientTypeId];
                const rawStatus = appointment[constants.uf.appointment.status];
                const status = constants.listFieldValues.appointment.statusById[rawStatus];
                // Наполняем объект
                const specialistData = schedule[specialistId] ??= {};
                const appointments = specialistData[startOfDay] ??= [];
                appointments.push({
                    id: appointment.id,
                    start,
                    end,
                    patient: {
                        id: patientId,
                        type: patientType
                    },
                    status,
                });
            }
        }
        return schedule;
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
        const params = {
            entityTypeId: constants.entityTypeId.workSchedule,
            filter: {
                [`>=${constants.uf.workSchedule.date}`]: from,
                [`<=${constants.uf.workSchedule.date}`]: to,
            },
            order: {[constants.uf.workSchedule.date]: 'ASC'}
        }
        const response = await this.bx.callListMethod('crm.item.list', params);
        const workSchedule = {};
        for ( const items of response ) {
            for ( const schedule of items.items ) {
                const specialistData = workSchedule[schedule.assignedById] ??= {};
                const date = new Date(schedule[constants.uf.workSchedule.date]);
                // date.setHours(0, 0, 0, 0);
                const data = specialistData[date] = {
                    id: schedule.id,
                    intervals: []
                };
                const rawIntervals = schedule[constants.uf.workSchedule.intervals] || [];
                for ( const interval of rawIntervals ) {
                    const [start, end] = interval.split(":");
                    data.intervals.push({ start: new Date(parseInt(start)), end: new Date(parseInt(end)) });
                }
            }
        }
        return workSchedule;
    }

    async getDeals(filter={}) {
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



class APIClientMock {
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

export const clientMock = new APIClientMock();

const apiClient = new APIClient();
export default apiClient;
