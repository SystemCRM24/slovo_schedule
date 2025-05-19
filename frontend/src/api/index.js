class APIClient {

    constructor() {
        this.serverUrl = 'https://3638421-ng03032.twc1.net/slovo_schedule_api/front/';
        this.testFrom = new Date('2025-04-27T21:00:00.000Z');
        this.testTo = new Date('2025-04-30T20:59:59.167Z');
    }

    async _delete(url) {
        const response = await fetch(url, {method: 'DELETE'});
        return await response.json();
    }

    async _get(url) {
        const response = await fetch(url);
        return await response.json();
    }

    async _post(url, body) {
        const init = {   
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(body)
        }
        const response = await fetch(url, init)
        return await response.json();
    }

    async _update(url, body) {
        const init = {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(body)
        };
        const response = await fetch(url, init);
        return await response.json();
    }

    createUrl(method, queries = null) {
        let url = `${this.serverUrl}${method}`;
        if ( queries !== null ) {
            const params = new URLSearchParams();
            for ( const [key, value] of Object.entries(queries) ) {
                params.append(key, value);
            }
            url += `?${params.toString()}`
        }
        return url;
    }

    /**
     * Получает Специалистов и возвращает Объект по следующему соглашению
     * @returns {Promise<Object.<string, { name: string, departments: number[] }>>}
     */
    async getSpecialists() {
        const response = await this._get(this.createUrl('get_specialist'));
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
        const url = this.createUrl('get_clients');
        const response = await this._get(url);
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
        const url = this.createUrl('get_schedules', {start: from.toISOString(), end: to.toISOString()});
        const response = await this._get(url);
        const data = {};
        for ( const item of response ) {
            const specialist = data[item.specialist_id] ??= {};
            const day = specialist[new Date(item.date)] ??= [];
            for ( const dayData of item.appointments ) {
                day.push({
                    ...dayData,
                    start: new Date(dayData.start),
                    end: new Date(dayData.end)
                });
            }
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
        const url = this.createUrl('get_work_schedules', {start: from.toISOString(), end: to.toISOString()});
        const response = await this._get(url);
        const data = {};
        for ( const item of response ) {
            const specialist = data[item.specialist_id] ??= {};
            const day = specialist[new Date(item.date)] ??= item.schedule;
            day.intervals.forEach(
                interval => {
                    interval.start = new Date(interval.start);
                    interval.end = new Date(interval.end);
                }
            );
        }
        return data;
    }

    async getDeals(filter = {}) {
        const deals = await this.bx.callListMethod('crm.deal.list', {'FILTER': filter});
        return deals;
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
        const url = this.createUrl('appointment/');
        const body = {
            ...data,
            start: data.start.toISOString(),
            end: data.end.toISOString(),
        }
        return await this._post(url, body);
    }

    /**
     * Получение информации о элементе смарт-процесса - расписания
     * @param {string} id
     */
    async getAppointment(id) {
        const url = this.createUrl('appointment/', {id});
        return await this._get(url);
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
        const url = this.createUrl('appointment/', {id});
        const body = {
            ...data,
            start: data.start.toISOString(),
            end: data.end.toISOString(),
        }
        return await this._update(url, body);
    }

    /**
     * Удаляет запись о приеме
     * @param {string} id - ид записи (Расписания)
     * @returns
     */
    async deleteAppointment(id) {
        const url = this.createUrl('appointment/', {id})
        return await this._delete(url);
    }

    /**
     * Создает элемент смарт-процесса - график
     * @param {object} data - Объект графика
     * @param {string} data.specialist - ИД специалиста
     * @param {string} data.date - дата, для которой нужно создать расписание
     * @param {Array<{start: Date, end: Date}>} data.intervals - Интервалы, которые обозначают рабочее время
     */
    async createWorkSchedule(data) {
        const url = this.createUrl('schedule/');
        const body = {
            specialist: data.specialist,
            date: data.date.toISOString(),
            intervals: data.intervals.map(i => `${i.start.getTime()}:${i.end.getTime()}`)
        };
        return await this._post(url, body);
    }

    /**
     * Получает элемент смарт-процесса - график
     * @param {string} id - ид графика
     */
    async getWorkSchedule(id) {
        const url = this.createUrl('schedule/', {id});
        return await this._get(url);
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
        const url = this.createUrl('schedule/', {id});
        const body = {
            ...data,
            intervals: data.intervals.map(i => `${i.start.getTime()}:${i.end.getTime()}`)
        };
        return await this._update(url, body);
    }

    /**
     * Удаляет запись о рабочем графике
     * @param {string} id - ид рабочего графика
     * @returns
     */
    async deleteWorkSchedule(id) {
        const url = this.createUrl('schedule/', {id});
        return await this._delete(url);
    }
}


const apiClient = new APIClient();
export default apiClient;
