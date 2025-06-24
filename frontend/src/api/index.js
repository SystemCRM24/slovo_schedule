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
                "L": "52", "LM": "54", "D1-3,5": "55", "D 3,5+": "56", "R": "57", "Z": "58",
                "A": "59", "NT": "60", "НДГ": "61", "NP": "62", "P": "63", "СИ": "64",
                "КИТ": "65", "АВА-Р": "66", "i": "67", "К": "68", "d": "69", "КК": "70",
                "d-ава": "71", "dNP": "72", "dd": "73", "dL": "74", "dP": "75"
            },
            codeById: {
                "52": "L", "54": "LM", "55": "D1-3,5", "56": "D 3,5+", "57": "R", "58": "Z",
                "59": "A", "60": "NT", "61": "НДГ", "62": "NP", "63": "P", "64": "СИ",
                "65": "КИТ", "66": "АВА-Р", "67": "i", "68": "К", "69": "d", "70": "КК",
                "71": "d-ава", "72": "dNP", "73": "dd", "74": "dL", "75": "dP"
            }
        }
    }
}


class APIClient {

    constructor() {
        this.serverUrl = 'https://3638421-ng03032.twc1.net/slovo_schedule_api/front/';
        // this.serverUrl = 'http://localhost:8000/front/';
        this.testFrom = new Date('2025-04-27T21:00:00.000Z');
        this.testTo = new Date('2025-04-30T20:59:59.167Z');
    }

    async delete(url) {
        const response = await fetch(url, {method: 'DELETE'});
        return await response.json();
    }

    async get(url) {
        const response = await fetch(url);
        return await response.json();
    }

    async post(url, body) {
        const init = {   
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(body)
        }
        const response = await fetch(url, init)
        return await response.json();
    }

    async update(url, body) {
        const init = {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(body)
        };
        const response = await fetch(url, init);
        return await response.json();
    }

    getUrl(method, queries = null) {
        let url = `${this.serverUrl}${method}`;
        if ( queries !== null ) {
            const params = new URLSearchParams();
            for ( const [key, value] of Object.entries(queries) ) {
                params.append(key, value);
            }
            url += `?${params.toString()}`;
        }
        return url;
    }

    /**
     * Получает Специалистов и возвращает Объект по следующему соглашению
     * @returns {Promise<Object.<string, { name: string, departments: number[] }>>}
     */
    async getSpecialists() {
        const response = await this.get(this.getUrl('get_specialist'));
        const data = {};
        for( const spec of response ) {
            data[spec.id] = spec;
        }
        return data;
    }

    /**
     * Получение детей.
     * @returns {Promise<Object.<string, string>>}
     */
    async getClients() {
        const url = this.getUrl('get_clients');
        const response = await this.get(url);
        const data = {};
        for ( const child of response ) {
            data[child.id] = child.full_name;
        }
        return data;
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
        const endOfTo = new Date(to);
        endOfTo.setDate(endOfTo.getDate() + 1)
        const url = this.getUrl('get_schedules', {start: from.toISOString(), end: endOfTo.toISOString()});
        const response = await this.get(url);
        const data = {};
        for ( const appointment of response ) {
            const specialist = data[appointment.specialist] ??= {};
            const start = new Date(appointment.start);
            const end = new Date(appointment.end);
            const startOfDay = new Date(start)
            startOfDay.setHours(3, 0, 0, 0);
            const day = specialist[startOfDay] ??= [];
            day.push({
                id: appointment.id,
                start,
                end,
                patient: {
                    id: appointment.patient, 
                    type: appointment.code
                },
                old_patient: appointment.old_patient
            });
        }
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
        const url = this.getUrl('get_work_schedules', {start: from.toISOString(), end: to.toISOString()});
        const response = await this.get(url);
        const data = {};
        for ( const item of response ) {
            const specialist = data[item.specialist] ??= {};
            const date = new Date(item.date);
            const dateObj = specialist[date] ??= {};
            dateObj.id = item.id;
            dateObj.intervals = item.intervals.map(
                i => {
                    const [start, end] = i.split(':').map(el => Number(el))
                    return {start: new Date(start), end: new Date(end)}
                }
            );
        }
        return data;
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
        const url = `${this.serverUrl}appointment/`
        // const url = this.getUrl('appointment/');
        const body = {
            specialist: data.specialist,
            patient: data.patient,
            start: data.start.toISOString(), 
            end: data.end.toISOString(), 
            status: data.status,
            code: data.code,
            old_patient: data.patient
        };

        if (!body.specialist || !body.patient || !body.start || !body.end || !body.code) {
            throw new Error('Все поля (specialist, patient, start, end, status, code) должны быть заполнены');
        }
        // if (!constants.listFieldValues.appointment.idByStatus[body.status]) {
        //     throw new Error(`Недопустимый статус: ${body.status}`);
        // }
        if (!constants.listFieldValues.appointment.idByCode[body.code]) {
            throw new Error(`Недопустимый код: ${body.code}`);
        }
        const response = await this.post(url, body);
        if (!response.id) {
            throw new Error(`Ошибка API: ${response}`);
        }
        return { id: response.id };
    }
    // TODO 
    // нужно ли преобразовывать start и end в Date ??
    // start: new Date(response.start),
    // end: new Date(response.end), 
    /**
     * Получение информации о элементе смарт-процесса - расписания
     * @param {string} id
     */
    async getAppointment(id) {
        const url = `${this.serverUrl}appointment/${id}`
        // const url = this.getUrl('appointment/', { id });

        const response = await this.get(url);

        if (!response.id) {
            throw new Error(`Запись с id=${id} не найдена`);
        }

        return {
            id: response.id,
            specialist: response.specialist,
            patient: response.patient,
            start: new Date(response.start),
            end: new Date(response.end), 
            status: response.status,
            code: response.code
        };
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
        const url = `${this.serverUrl}appointment/${id}`
        // const url = this.getUrl('appointment/', { id });
        const body = {
            id: data.id,
            specialist: data.specialist,
            patient: data.patient,
            start: data.start.toISOString(),
            end: data.end.toISOString(),
            status: data.status,
            code: data.code,
            old_patient: data.old_patient
        };
        
        if (!body.specialist || !body.patient || !body.start || !body.end || !body.code) {
            throw new Error('Все поля (specialist, patient, start, end, status, code) должны быть заполнены');
        }
        // if (!constants.listFieldValues.appointment.idByStatus[body.status]) {
        //     throw new Error(`Недопустимый статус: ${body.status}`);
        // }
        if (!constants.listFieldValues.appointment.idByCode[body.code]) {
            throw new Error(`Недопустимый код: ${body.code}`);
        }

        const response = await this.update(url, body);
        
        if (!response.id) {
            throw new Error(`Ошибка API: ${response}`);
        }

        return { id: response.id };
    }

    /**
     * Удаляет запись о приеме
     * @param {string} id - ид записи (Расписания)
     * @returns
     */
    async deleteAppointment(id) {
        const url = `${this.serverUrl}appointment/${id}`
        // const url = this.getUrl('appointment/', {id})
        return await this.delete(url);
    }

    /**
     * Создает элемент смарт-процесса - график
     * @param {object} data - Объект графика
     * @param {string} data.specialist - ИД специалиста
     * @param {string} data.date - дата, для которой нужно создать расписание
     * @param {Array<{start: Date, end: Date}>} data.intervals - Интервалы, которые обозначают рабочее время
     */
    async createWorkSchedule(data) {
        const url = this.getUrl('schedule/');
        const body = {
            specialist: data.specialist,
            date: data.date.toISOString(),
            intervals: data.intervals.map(i => `${i.start.getTime()}:${i.end.getTime()}`)
        };
        return await this.post(url, body);
    }

    /**
     * Получает элемент смарт-процесса - график
     * @param {string} id - ид графика
     */
    async getWorkSchedule(id) {
        const url = this.getUrl('schedule/', {id});
        return await this.get(url);
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
        const url = this.getUrl('schedule/', {id});
        const body = {
            ...data,
            intervals: data.intervals.map(i => `${i.start.getTime()}:${i.end.getTime()}`)
        };
        return await this.update(url, body);
    }

    /**
     * Удаляет запись о рабочем графике
     * @param {string} id - ид рабочего графика
     * @returns
     */
    async deleteWorkSchedule(id) {
        const url = this.getUrl('schedule/', {id});
        return await this.delete(url);
    }
}


const apiClient = new APIClient();

export default apiClient;