export const constants = {
    entityTypeId: {appointment: 1036, workSchedule: 1042},
    departments: {
        "71": "А", "59": "АБА", "60": "АБА-К", "82": "АВС", "84": "Б-трэйн", "78": "БАК", "77": "БОС", "67": "Д1",
        "68": "Д2", "53": "дАБА", "55": "дЗ", "56": "дИПР", "52": "дКНП", "90": "дКПс", "50": "дЛ", "51": "дНП",
        "57": "дПС", "54": "дСИ", "85": "ДЭНАС", "69": "З", "70": "З-в", "89": "З-гр", "62": "ИПР", "61": "КФ", "64": "Л",
        "65": "Л-В", "66": "ЛМ", "76": "ЛР", "86": "Н-порт", "72": "НДГ", "87": "НЭК", "63": "ПРР", "74": "ПС-в",
        "73": "ПС-д", "75": "Р", "88": "РТ", "58": "СИ", "80": "СС", "79": "ТТ", "81": "Форб", "91": "ПШ", "92": "КЛ",
        "93": "ДРЗ", "94": "СК"
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
                "Л": "52", "ЛМ": "54", "Д1": "55", "Р": "57", "З": "58", "А": "59",
                "НДГ": "61", "СИ": "64", "дАБА": "71", "дНП": "72", "дЛ": "74",
                "АБА": "2333", "АБА-К": "2334", "АВС": "2335", "Б-трэйн": "2336", "БАК": "2337", "БОС": "2338",
                "Д2": "2339", "дЗ": "2340", "дИПР": "2341", "дКНП": "2342", "дПС": "2343", "дСИ": "2344",
                "ДЭНАС": "2345", "З-в": "2346", "З-гр": "2347", "ИПР": "2348", "КФ": "2349", "Л-В": "2350",
                "ЛР": "2351", "Н-порт": "2352", "НЭК": "2353", "ПРР": "2354", "ПС-в": "2355", "ПС-д": "2356",
                "РТ": "2357", "СС": "2358", "ТТ": "2359", "Форб": "2361", "дКПс": "2363", "ПШ": "2364", "СК": "2365",
                "ДРЗ": "2366", "КЛ": "2367"
            },
            codeById: {
                "52": "Л", "54": "ЛМ", "55": "Д1", "57": "Р", "58": "З", "59": "А",
                "61": "НДГ", "64": "СИ", "71": "дАБА", "72": "дНП", "74": "дЛ",
                "2333": "АБА", "2334": "АБА-К", "2335": "АВС", "2336": "Б-трэйн", "2337": "БАК", "2338": "БОС",
                "2339": "Д2", "2340": "дЗ", "2341": "дИПР", "2342": "дКНП", "2343": "дПС", "2344": "дСИ",
                "2345": "ДЭНАС", "2346": "З-в", "2347": "З-гр", "2348": "ИПР", "2349": "КФ", "2350": "Л-В",
                "2351": "ЛР", "2352": "Н-порт", "2353": "НЭК", "2354": "ПРР", "2355": "ПС-в", "2356": "ПС-д",
                "2357": "РТ", "2358": "СС", "2359": "ТТ", "2361": "Форб", "2363": "дКПс", "2364": "ПШ", "2365": "СК",
                "2366": "ДРЗ", "ДРЗ": "2367"
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
        // return await response.json();
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
        console.log('[DEBUG]', from, to);
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
                patient: {id: appointment.patient, type: appointment.code},
                status: appointment.status,
                abonnement: appointment.abonnement,
                old_specialist: appointment.old_specialist,
                old_start: appointment.old_start !== null ? new Date(appointment.old_start) : null,
                old_end: appointment.old_end !== null ? new Date(appointment.old_end) : null,
                old_patient: appointment.old_patient,
                old_code: appointment.old_code,
                old_status: appointment.old_status,
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
        };
        const response = await this.post(url, body);
        if (!response.id) {
            throw new Error(`Ошибка API: ${response}`);
        }
        return response;
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
     * @param {string} data.code - код занятия
     */
    async updateAppointment(id, data) {
        const url = `${this.serverUrl}appointment/${id}`
        const body = {
            specialist: data.specialist,
            patient: data.patient,
            start: data.start.toISOString(),
            end: data.end.toISOString(),
            code: data.code,
        };
        const response = await this.update(url, body);
        if (!response.id) {
            throw new Error(`Ошибка API: ${response}`);
        }
        response.start = new Date(response.start);
        response.end = new Date(response.end);
        response.old_start = new Date(response.old_start);
        response.old_end = new Date(response.old_end);
        return response;
    }

    async updateAppointmentMassive(id, data) {
        const url = `${this.serverUrl}appointment/massive/${id}`;
        const body = {
            specialist: data.specialist,
            patient: data.patient,
            start: data.start.toISOString(),
            end: data.end.toISOString(),
            code: data.code,
            status: data.status,
        };
        const response = await this.update(url, body);
        return response;
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

    async rollbackAppointment(id) {
        const url = `${this.serverUrl}appointment/rollback/${id}`;
        const init = {method: 'PUT', headers: {'Content-Type': 'application/json'}};
        const response = await fetch(url, init);
        return await response.json();
    }

    /**
     * Удаляет запись о приеме (на год вперед)
     * @param {string} id - ид записи (Расписания)
     * @returns
     */
    async deleteAppointmentMassive(id) {
        const url = `${this.serverUrl}appointment/massive/${id}`
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
        const url = `${this.serverUrl}schedule/`
        // const url = this.getUrl('schedule/');
        const body = {
            specialist: data.specialist,
            date: data.date.toISOString(),
            intervals: data.intervals.map(i => `${i.start.getTime()}:${i.end.getTime()}`)
        };
        return await this.post(url, body);
    }

    /**
     * Создает элемент смарт-процесса - график (на год вперед)
     * @param {object} data - Объект графика
     * @param {string} data.specialist - ИД специалиста
     * @param {string} data.date - дата, для которой нужно создать расписание
     * @param {Array<{start: Date, end: Date}>} data.intervals - Интервалы, которые обозначают рабочее время
     */
    async createWorkScheduleMassive(data) {
        const url = `${this.serverUrl}schedule/massive/`
        // const url = this.getUrl('schedule/');
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
        const url = `${this.serverUrl}schedule/${id}`
        // const url = this.getUrl('schedule/', {id});
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
        const url = `${this.serverUrl}schedule/${id}`
        // const url = this.getUrl('schedule/', {id});
        const body = {
            ...data,
            intervals: data.intervals.map(i => `${i.start.getTime()}:${i.end.getTime()}`)
        };
        return await this.update(url, body);
    }

    /**
     * Обновляет элемент смарт-процесса-график (на год вперед)
     * @param {string} id - ид графика
     * @param {object} data - Объект графика
     * @param {string} data.specialist - ИД специалиста
     * @param {string} data.date - дата, для которой нужно создать расписание
     * @param {Array<{start: Date, end: Date}>} data.intervals - Интервалы, которые обозначают рабочее время
     */
    async updateWorkScheduleMassive(id, data) {
        const url = `${this.serverUrl}schedule/massive/${id}`
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
        const url = `${this.serverUrl}schedule/${id}`
        // const url = this.getUrl('schedule/', {id});
        return await this.delete(url);
    }

    /**
     * Удаляет запись о рабочем графике (на год вперед)
     * @param {string} id - ид рабочего графика
     * @returns
     */
    async deleteWorkScheduleMassive(id) {
        const url = `${this.serverUrl}schedule/massive/${id}`
        return await this.delete(url);
    }

    /**
     * Обновляет константные значения.-
     */
    async updateConstants() {
        const url = this.getUrl('get_constants');
        const response = await this.get(url);
        response.departments && (constants.departments = response.departments);
        const codeById = response?.appointment?.lfv?.codeById;
        if ( codeById ) {
            constants.listFieldValues.appointment.codeById = codeById;
        }
        const idByCode = response?.appointment?.lfv?.idByCode;
        if ( idByCode ) {
            constants.listFieldValues.appointment.idByCode = idByCode;
        }
    }

    async cancelAnonnement(id, date) {
        const url = `${this.serverUrl}appointment/cancel_abonnement/${id}`;
        const params = date ? {date: date.toISOString()} : {date: date}
        const response = await this.update(url, params);
        return response;
    }
}


const apiClient = new APIClient();

export default apiClient;